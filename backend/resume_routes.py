import os
import re
import json
import PyPDF2
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file
import io
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, User, Student
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from google_drive_service import (
    drive_configured,
    upload_file as upload_file_to_drive,
    download_file as download_drive_file,
    delete_file as delete_drive_file,
    extract_file_id as extract_drive_file_id,
)

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Gemini API
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False

GEMINI_AVAILABLE = GEMINI_SDK_AVAILABLE or HTTPX_AVAILABLE


def _normalize_gemini_model_name(model_name: str | None) -> str:
    name = (model_name or '').strip()
    if not name:
        return 'gemini-1.5-flash'

    # Allow users to paste full resource names or accidental URL-ish values.
    # Examples:
    # - models/gemini-2.0-flash
    # - https://.../v1beta/models/gemini-2.0-flash
    if '/' in name:
        name = name.rstrip('/')
        name = name.split('/')[-1]

    # Common misconfigurations like "v1.5-flash" or "1.5-flash" should map to
    # the actual model id "gemini-1.5-flash".
    m = re.fullmatch(r'v?(\d+(?:\.\d+)?)-(flash|pro)', name, flags=re.IGNORECASE)
    if m:
        return f'gemini-{m.group(1)}-{m.group(2).lower()}'

    # Tolerate "gemini 3 flash" style.
    name = re.sub(r'\s+', '-', name)
    name = name.replace('--', '-')
    return name


def _gemini_error_message(exc: Exception) -> str:
    """Return a safe error message without leaking URLs or API keys."""
    # httpx HTTP errors can include the full request URL (with ?key=...), so do not
    # surface str(exc) to the client.
    if HTTPX_AVAILABLE:
        try:
            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code if exc.response is not None else None
                detail = None
                try:
                    payload = exc.response.json() if exc.response is not None else None
                    detail = (
                        payload.get('error', {})
                        .get('message')
                        if isinstance(payload, dict)
                        else None
                    )
                except Exception:
                    detail = None
                if status:
                    return f'Gemini request failed (HTTP {status})' + (f": {detail}" if detail else '')
                return 'Gemini request failed'
        except Exception:
            pass
    return 'Gemini request failed'


def gemini_generate_text(prompt: str, api_key: str, model_name: str | None = None) -> str:
    """Generate text using Gemini.

    Uses google-generativeai SDK when available, otherwise falls back to REST via httpx.
    """
    if not api_key:
        raise RuntimeError('Gemini API key not configured')

    model_name = _normalize_gemini_model_name(model_name)

    # Try the requested model first, then fall back to known-good flash models.
    # The exact best model varies by account/region and API version.
    fallback_models = [
        'gemini-3-flash',
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-flash',
    ]
    model_candidates = [model_name] + [m for m in fallback_models if m != model_name]

    if GEMINI_SDK_AVAILABLE:
        genai.configure(api_key=api_key)
        last_error: Exception | None = None
        for m in model_candidates:
            try:
                model = genai.GenerativeModel(m)
                response = model.generate_content(prompt)
                text = (getattr(response, 'text', None) or '').strip()
                if not text:
                    raise RuntimeError('Gemini returned empty text')
                return text
            except Exception as e:
                last_error = e
        raise RuntimeError(_gemini_error_message(last_error or RuntimeError('Gemini request failed')))

    if not HTTPX_AVAILABLE:
        raise RuntimeError('Gemini client not available (missing httpx)')

    def _call(model: str):
        model_path = model
        if not model_path.startswith('models/'):
            model_path = f'models/{model_path}'
        url = f'https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent'
        params = {'key': api_key}
        payload = {
            'contents': [
                {
                    'role': 'user',
                    'parts': [{'text': prompt}],
                }
            ]
        }
        with httpx.Client(timeout=30.0) as client:
            r = client.post(url, params=params, json=payload)
            try:
                r.raise_for_status()
            except Exception as e:
                # Re-raise as HTTPStatusError (if possible) so we can sanitize.
                raise
            return r.json()

    last_error: Exception | None = None
    for m in model_candidates:
        try:
            data = _call(m)
            break
        except Exception as e:
            last_error = e
            continue
    else:
        raise RuntimeError(_gemini_error_message(last_error or RuntimeError('Gemini request failed')))

    candidates = data.get('candidates') or []
    if not candidates:
        raise RuntimeError('Gemini returned no candidates')
    content = (candidates[0].get('content') or {})
    parts = content.get('parts') or []
    text_parts = [p.get('text', '') for p in parts if isinstance(p, dict)]
    text = ''.join(text_parts).strip()
    if not text:
        raise RuntimeError('Gemini returned empty text')
    return text

resume_bp = Blueprint('resume', __name__)

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads' / 'resumes'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ''

def extract_text_from_pdf_bytes(content):
    try:
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
        return text
    except Exception as e:
        print(f"Error extracting PDF bytes: {e}")
        return ''

def get_stored_resume_bytes(student):
    """Fetch resume bytes from Drive if available, otherwise local storage."""
    drive_id = getattr(student, 'resume_drive_file_id', None) or extract_drive_file_id(student.resume_url)
    if drive_id:
        data = download_drive_file(drive_id)
        if data:
            return data, 'drive'
    if student.resume_url:
        filename = student.resume_url.split('/')[-1]
        filepath = UPLOAD_FOLDER / filename
        if filepath.exists():
            try:
                return filepath.read_bytes(), 'local'
            except Exception as e:
                print(f"Local resume read failed: {e}")
    return None, None

def get_resume_text(student):
    resume_bytes, source = get_stored_resume_bytes(student)
    if not resume_bytes:
        return '', 'Resume file not found'
    text = extract_text_from_pdf_bytes(resume_bytes)
    if not text.strip():
        return '', 'Could not extract text from resume'
    return text, None

def parse_resume_data(text):
    """Extract structured data from resume text"""
    data = {}
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        data['email'] = emails[0]
    
    # Extract phone number (Indian format)
    phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
    phones = re.findall(phone_pattern, text)
    if phones:
        data['phone'] = phones[0].strip()
    
    # Extract LinkedIn URL
    linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
    linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
    if linkedin:
        data['linkedin_url'] = linkedin[0]
    
    # Extract GitHub URL
    github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+'
    github = re.findall(github_pattern, text, re.IGNORECASE)
    if github:
        data['github_url'] = github[0]
    
    # Extract skills (common programming languages and technologies)
    skills_keywords = [
        'Python', 'Java', 'JavaScript', 'C\\+\\+', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin',
        'React', 'Angular', 'Vue', 'Node\\.js', 'Django', 'Flask', 'Spring', 'Express',
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Firebase',
        'HTML', 'CSS', 'SASS', 'Bootstrap', 'Tailwind',
        'Git', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
        'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
        'REST API', 'GraphQL', 'Microservices'
    ]
    
    found_skills = []
    for skill in skills_keywords:
        if re.search(skill, text, re.IGNORECASE):
            found_skills.append(skill.replace('\\', ''))
    
    if found_skills:
        data['skills'] = ', '.join(list(set(found_skills)))
    
    # Extract CGPA/GPA
    cgpa_pattern = r'(?:CGPA|GPA)[\s:]*([0-9]\.[0-9]{1,2})'
    cgpa_matches = re.findall(cgpa_pattern, text, re.IGNORECASE)
    if cgpa_matches:
        try:
            data['cgpa'] = float(cgpa_matches[0])
        except:
            pass
    
    # Extract 10th percentage
    tenth_pattern = r'(?:10th|10|Xth|X|SSC|Secondary)[\s\w]*[\s:]*([0-9]{1,3}\.?[0-9]*)[\s]*%'
    tenth_matches = re.findall(tenth_pattern, text, re.IGNORECASE)
    if tenth_matches:
        try:
            data['tenth_percentage'] = float(tenth_matches[0])
        except:
            pass
    
    # Extract 12th percentage
    twelfth_pattern = r'(?:12th|12|XIIth|XII|HSC|Senior Secondary)[\s\w]*[\s:]*([0-9]{1,3}\.?[0-9]*)[\s]*%'
    twelfth_matches = re.findall(twelfth_pattern, text, re.IGNORECASE)
    if twelfth_matches:
        try:
            data['twelfth_percentage'] = float(twelfth_matches[0])
        except:
            pass
    
    # Extract sections (experience, projects, certifications)
    # Experience section
    experience_pattern = r'(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE)(.*?)(?:PROJECTS|EDUCATION|SKILLS|CERTIFICATIONS|$)'
    experience_match = re.search(experience_pattern, text, re.IGNORECASE | re.DOTALL)
    if experience_match:
        data['experience'] = experience_match.group(1).strip()[:500]  # Limit to 500 chars
    
    # Projects section
    projects_pattern = r'(?:PROJECTS|ACADEMIC PROJECTS|PERSONAL PROJECTS)(.*?)(?:EXPERIENCE|EDUCATION|SKILLS|CERTIFICATIONS|$)'
    projects_match = re.search(projects_pattern, text, re.IGNORECASE | re.DOTALL)
    if projects_match:
        data['projects'] = projects_match.group(1).strip()[:500]
    
    # Certifications section
    cert_pattern = r'(?:CERTIFICATIONS|CERTIFICATES|ACHIEVEMENTS)(.*?)(?:EXPERIENCE|PROJECTS|EDUCATION|SKILLS|$)'
    cert_match = re.search(cert_pattern, text, re.IGNORECASE | re.DOTALL)
    if cert_match:
        data['certifications'] = cert_match.group(1).strip()[:500]
    
    return data

@resume_bp.route('/api/student/upload-resume', methods=['POST'])
@jwt_required()
def upload_resume():
    """Upload and parse resume"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF, DOC, DOCX allowed'}), 400
        
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({'error': 'Empty file'}), 400
        
        filename = secure_filename(f"resume_{student.id}_{file.filename}")
        parsed_data = {}
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf_bytes(file_bytes)
            print(f"Extracted text length: {len(text)}")
            parsed_data = parse_resume_data(text)
            print(f"Parsed data: {parsed_data}")
        
        storage = 'local'
        resume_url = None
        if drive_configured():
            drive_file = upload_file_to_drive(file_bytes, filename, file.mimetype, folder_id=DRIVE_FOLDER_ID)
            if drive_file:
                resume_url = drive_file.get('webViewLink') or drive_file.get('webContentLink')
                storage = 'drive'
                if hasattr(student, 'resume_storage_provider'):
                    student.resume_storage_provider = 'drive'
                if hasattr(student, 'resume_drive_file_id'):
                    student.resume_drive_file_id = drive_file.get('id')
                if hasattr(student, 'resume_drive_web_view_link'):
                    student.resume_drive_web_view_link = drive_file.get('webViewLink')
                if hasattr(student, 'resume_filename'):
                    student.resume_filename = drive_file.get('name') or filename
                if hasattr(student, 'resume_updated_at'):
                    student.resume_updated_at = datetime.utcnow()
        
        if not resume_url:
            filepath = UPLOAD_FOLDER / filename
            filepath.write_bytes(file_bytes)
            resume_url = f"/uploads/resumes/{filename}"
            storage = 'local'
            if hasattr(student, 'resume_storage_provider'):
                student.resume_storage_provider = 'local'
            if hasattr(student, 'resume_drive_file_id'):
                student.resume_drive_file_id = None
            if hasattr(student, 'resume_drive_web_view_link'):
                student.resume_drive_web_view_link = None
            if hasattr(student, 'resume_filename'):
                student.resume_filename = filename
            if hasattr(student, 'resume_updated_at'):
                student.resume_updated_at = datetime.utcnow()
        
        # Update student record
        student.resume_url = resume_url
        db.session.commit()
        
        return jsonify({
            'message': 'Resume uploaded successfully',
            'resume_url': student.resume_url,
            'parsed_data': parsed_data,
            'storage': storage
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/api/student/parse-resume', methods=['POST'])
@jwt_required()
def parse_resume_endpoint():
    """Parse an already uploaded resume"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        if not student.resume_url:
            return jsonify({'error': 'No resume uploaded yet'}), 400
        
        resume_text, error = get_resume_text(student)
        if error:
            status = 404 if 'not found' in error.lower() else 400
            return jsonify({'error': error}), status
        
        parsed_data = parse_resume_data(resume_text) if resume_text else {}
        return jsonify({'parsed_data': parsed_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/api/student/delete-resume', methods=['DELETE'])
@jwt_required()
def delete_resume():
    """Delete uploaded resume"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        if not student.resume_url:
            return jsonify({'error': 'No resume to delete'}), 400
        
        drive_deleted = False
        drive_id = getattr(student, 'resume_drive_file_id', None) or extract_drive_file_id(student.resume_url)
        if drive_id:
            drive_deleted = delete_drive_file(drive_id)
        
        # Construct file path for local fallback
        filename = student.resume_url.split('/')[-1]
        filepath = UPLOAD_FOLDER / filename
        if filepath.exists():
            filepath.unlink()
        
        # Update student record
        student.resume_url = None
        if hasattr(student, 'resume_storage_provider'):
            student.resume_storage_provider = 'local'
        if hasattr(student, 'resume_drive_file_id'):
            student.resume_drive_file_id = None
        if hasattr(student, 'resume_drive_web_view_link'):
            student.resume_drive_web_view_link = None
        if hasattr(student, 'resume_filename'):
            student.resume_filename = None
        if hasattr(student, 'resume_updated_at'):
            student.resume_updated_at = None
        student.ats_score = None
        student.ats_feedback = None
        student.ats_calculated_at = None
        db.session.commit()
        
        return jsonify({
            'message': 'Resume deleted successfully',
            'drive_deleted': drive_deleted
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def calculate_ats_with_gemini(resume_text):
    """Calculate ATS score using Gemini API"""
    if not GEMINI_AVAILABLE:
        return None, "Gemini API not available"
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'YOUR_GEMINI_API_KEY_HERE':
        return None, "Gemini API key not configured"
    
    try:
        # Prefer configuration; default to a fast flash model.
        model_name = os.getenv('GEMINI_MODEL', 'gemini-3-flash')
        
        prompt = f'''You are an expert ATS (Applicant Tracking System) analyzer. Analyze this resume and provide realistic feedback.

IMPORTANT RULES FOR KEYWORDS:
- Keywords must be SHORT (1-3 words max) - like "Python", "AWS", "Machine Learning", "React"
- DO NOT use long phrases like "automatic data collection and curation systems"
- Focus only on: Programming languages, Frameworks, Tools, Platforms, Soft skills, Certifications
- Ignore job titles, seniority levels, and verbose descriptions

Resume Text:
{resume_text[:5000]}

Scoring Criteria (be realistic, most resumes score 50-80):
- Keyword optimization (20%) - Common tech skills present
- Format and structure (20%) - Clear sections, bullet points
- Skills relevance (20%) - Relevant technical skills
- Experience presentation (20%) - Quantified achievements
- Education (10%) - Degree, certifications
- Contact info (10%) - Email, phone, LinkedIn

Respond in JSON format ONLY (no markdown, no code blocks):
{{"score": 68, "strengths": ["Clear contact info", "Good skills section", "Quantified achievements"], "improvements": ["Add more action verbs", "Include certifications", "Add LinkedIn profile"], "missing_keywords": ["AWS", "Docker", "Git", "Agile", "REST API"], "formatting_tips": ["Use consistent bullet points", "Add projects section"], "overall": "Solid resume with good structure. Add cloud technologies and DevOps skills to improve ATS compatibility."}}'''
        
        response_text = gemini_generate_text(prompt, api_key=api_key, model_name=model_name).strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        result = json.loads(response_text)
        
        score = min(100, max(0, int(result.get('score', 50))))
        
        feedback = {
            'strengths': result.get('strengths', []),
            'improvements': result.get('improvements', []),
            'missing_keywords': result.get('missing_keywords', []),
            'formatting_tips': result.get('formatting_tips', []),
            'overall': result.get('overall', '')
        }
        
        return score, json.dumps(feedback)
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None, _gemini_error_message(e)


def calculate_ats_with_jd(resume_text, jd_text):
    """Calculate ATS score by comparing resume against a specific Job Description"""
    if not GEMINI_AVAILABLE:
        return None, "Gemini API not available"
    
    # Force reload .env
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'YOUR_GEMINI_API_KEY_HERE':
        return None, "Gemini API key not configured"
    
    try:
        model_name = os.getenv('GEMINI_MODEL', 'gemini-3-flash')
        
        prompt = f'''You are an expert ATS analyzer comparing a resume against a job description.

CRITICAL RULES FOR KEYWORDS:
1. Keywords MUST be SHORT (1-3 words maximum)
2. Use single technology/skill names like: "Python", "AWS", "Docker", "React", "SQL", "Kubernetes"
3. NEVER use long phrases from JD like "automatic data collection and curation systems"
4. NEVER include job titles like "Senior", "Lead", "Manager" as keywords
5. Extract only: Programming languages, Frameworks, Tools, Cloud platforms, Databases, Methodologies
6. Be realistic - most candidates match 40-75% of job requirements

**JOB DESCRIPTION:**
{jd_text[:3000]}

**RESUME:**
{resume_text[:4000]}

Analyze and provide:
- Score (0-100): Realistic match percentage. Entry-level: 40-60, Mid-level: 55-75, Senior matching: 70-90
- Matching Keywords: ONLY short skill/tech names found in BOTH resume and JD
- Missing Keywords: ONLY short skill/tech names in JD but NOT in resume (max 10 most important)
- Strengths: Brief points on what matches well
- Improvements: Brief actionable suggestions
- Overall: 1-2 sentence summary

Respond in JSON format ONLY (no markdown, no code blocks):
{{"score": 62, "strengths": ["Strong Python experience", "Relevant ML projects", "Good education background"], "improvements": ["Add cloud platform experience", "Include containerization skills", "Mention CI/CD experience"], "missing_keywords": ["AWS", "Docker", "Kubernetes", "Terraform", "Jenkins", "Spark"], "matching_keywords": ["Python", "SQL", "Machine Learning", "TensorFlow", "Git"], "formatting_tips": ["Add DevOps section", "Highlight scalability experience"], "overall": "Good foundation with 62% match. Strong in core ML skills but needs cloud/DevOps experience for this role."}}'''
        
        response_text = gemini_generate_text(prompt, api_key=api_key, model_name=model_name).strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        result = json.loads(response_text)
        
        score = min(100, max(0, int(result.get('score', 50))))
        
        feedback = {
            'strengths': result.get('strengths', []),
            'improvements': result.get('improvements', []),
            'missing_keywords': result.get('missing_keywords', []),
            'matching_keywords': result.get('matching_keywords', []),
            'formatting_tips': result.get('formatting_tips', []),
            'overall': result.get('overall', '')
        }
        
        return score, json.dumps(feedback)
        
    except Exception as e:
        print(f"Gemini API error (JD analysis): {e}")
        return None, _gemini_error_message(e)


@resume_bp.route('/api/student/calculate-ats', methods=['POST'])
@jwt_required()
def calculate_ats_score():
    """Calculate ATS score for uploaded resume using Gemini API"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        if not student.resume_url:
            return jsonify({'error': 'No resume uploaded yet'}), 400
        
        resume_text, error = get_resume_text(student)
        if error:
            status = 404 if 'not found' in error.lower() else 400
            return jsonify({'error': error}), status
        
        # Calculate ATS score using Gemini
        score, feedback = calculate_ats_with_gemini(resume_text)
        
        if score is None:
            return jsonify({
                'error': f'ATS calculation failed: {feedback}',
                'fallback_score': 50,
                'fallback_feedback': json.dumps({
                    'overall': 'ATS score could not be calculated. Please check if your Gemini API key is configured correctly.',
                    'strengths': [],
                    'improvements': ['Unable to analyze - API configuration issue'],
                    'missing_keywords': [],
                    'formatting_tips': []
                })
            }), 200
        
        # Save to database
        student.ats_score = score
        student.ats_feedback = feedback
        student.ats_calculated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ats_score': score,
            'ats_feedback': json.loads(feedback),
            'calculated_at': student.ats_calculated_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/api/student/analyze-resume-upload', methods=['POST'])
@jwt_required()
def analyze_resume_upload():
    """Upload a resume file directly for ATS analysis (separate from profile resume)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported for ATS analysis'}), 400
        
        # Read PDF directly from memory without saving
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            resume_text = ''
            for page in pdf_reader.pages:
                resume_text += page.extract_text() or ''
        except Exception as e:
            return jsonify({'error': f'Could not read PDF file: {str(e)}'}), 400
        
        if not resume_text.strip():
            return jsonify({'error': 'Could not extract text from PDF. Make sure it is not a scanned image.'}), 400
        
        print(f"Extracted {len(resume_text)} characters from resume")
        
        # Calculate ATS score using Gemini
        score, feedback = calculate_ats_with_gemini(resume_text)
        
        if score is None:
            return jsonify({
                'error': f'ATS calculation failed: {feedback}',
                'fallback_score': 50,
                'fallback_feedback': {
                    'overall': 'ATS score could not be calculated. Please check if your Gemini API key is configured correctly.',
                    'strengths': [],
                    'improvements': ['Unable to analyze - API configuration issue'],
                    'missing_keywords': [],
                    'formatting_tips': []
                }
            }), 200
        
        # Save to database
        student.ats_score = score
        student.ats_feedback = feedback
        student.ats_calculated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ats_score': score,
            'ats_feedback': json.loads(feedback),
            'calculated_at': student.ats_calculated_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in analyze_resume_upload: {e}")
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/api/student/analyze-with-jd', methods=['POST'])
@jwt_required()
def analyze_resume_with_jd():
    """Analyze resume against a specific Job Description for targeted ATS scoring"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        # Get resume - either from upload or from profile
        resume_text = ""
        
        if 'resume' in request.files and request.files['resume'].filename:
            # Resume uploaded directly
            file = request.files['resume']
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'Only PDF files are supported'}), 400
            
            try:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    resume_text += page.extract_text() or ''
            except Exception as e:
                return jsonify({'error': f'Could not read PDF file: {str(e)}'}), 400
        else:
            # Use profile resume
            if not student.resume_url:
                return jsonify({'error': 'Please upload a resume or add one to your profile'}), 400
            resume_text, error = get_resume_text(student)
            if error:
                status = 404 if 'not found' in error.lower() else 400
                return jsonify({'error': error}), status
        
        if not resume_text.strip():
            return jsonify({'error': 'Could not extract text from resume'}), 400
        
        # Get Job Description - either from file or text
        jd_text = ""
        
        if 'jd_file' in request.files and request.files['jd_file'].filename:
            # JD uploaded as PDF
            jd_file = request.files['jd_file']
            if jd_file.filename.lower().endswith('.pdf'):
                try:
                    pdf_reader = PyPDF2.PdfReader(jd_file)
                    for page in pdf_reader.pages:
                        jd_text += page.extract_text() or ''
                except Exception as e:
                    return jsonify({'error': f'Could not read JD PDF: {str(e)}'}), 400
            else:
                # Try reading as text
                jd_text = jd_file.read().decode('utf-8', errors='ignore')
        elif 'jd_text' in request.form and request.form['jd_text'].strip():
            # JD provided as text
            jd_text = request.form['jd_text']
        else:
            return jsonify({'error': 'Please provide a Job Description (text or PDF file)'}), 400
        
        if not jd_text.strip():
            return jsonify({'error': 'Could not extract text from Job Description'}), 400
        
        print(f"Resume: {len(resume_text)} chars, JD: {len(jd_text)} chars")
        
        # Calculate ATS score with JD comparison
        score, feedback = calculate_ats_with_jd(resume_text, jd_text)
        
        if score is None:
            return jsonify({
                'error': f'ATS calculation failed: {feedback}',
                'fallback_score': 50,
                'fallback_feedback': {
                    'overall': 'Analysis could not be completed. Please check API configuration.',
                    'strengths': [],
                    'improvements': [],
                    'missing_keywords': [],
                    'matching_keywords': [],
                    'formatting_tips': []
                }
            }), 200
        
        return jsonify({
            'success': True,
            'ats_score': score,
            'ats_feedback': json.loads(feedback),
            'analysis_type': 'jd_comparison',
            'calculated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in analyze_resume_with_jd: {e}")
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/api/student/resume/download', methods=['GET'])
@jwt_required()
def download_profile_resume():
    """Download (or inline-view) the student's stored resume.

    This works for both local uploads and Google Drive storage without requiring
    the client to access Drive directly.
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403

        student = user.student
        if not student or not student.resume_url:
            return jsonify({'error': 'No resume uploaded'}), 404

        resume_bytes, source = get_stored_resume_bytes(student)
        if not resume_bytes:
            return jsonify({'error': 'Resume not found'}), 404

        inline = request.args.get('inline', '1') in ('1', 'true', 'yes')

        filename = 'resume.pdf'
        try:
            if student.resume_url and '/uploads/resumes/' in student.resume_url:
                filename = student.resume_url.split('/uploads/resumes/')[-1] or filename
            elif student.resume_url and student.resume_url.startswith('http'):
                # If it's a Drive link, keep a generic filename
                filename = 'resume.pdf'
        except Exception:
            filename = 'resume.pdf'

        file_obj = io.BytesIO(resume_bytes)
        file_obj.seek(0)

        try:
            return send_file(
                file_obj,
                mimetype='application/pdf',
                as_attachment=not inline,
                download_name=filename,
                max_age=0,
            )
        except TypeError:
            # Flask < 2.0 compatibility
            return send_file(
                file_obj,
                mimetype='application/pdf',
                as_attachment=not inline,
                attachment_filename=filename,
                cache_timeout=0,
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@resume_bp.route('/api/test-gemini', methods=['GET'])
def test_gemini():
    """Test endpoint to check Gemini API configuration"""
    # Force reload .env
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)
    
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    
    result = {
        'gemini_available': GEMINI_AVAILABLE,
        'gemini_sdk_available': GEMINI_SDK_AVAILABLE,
        'httpx_available': HTTPX_AVAILABLE,
        'api_key_configured': bool(api_key and api_key != 'YOUR_GEMINI_API_KEY_HERE' and len(api_key) > 30),
        'api_key_length': len(api_key) if api_key else 0,
        'model_name': model_name,
        'env_path': str(env_path),
        'env_exists': env_path.exists()
    }
    
    if GEMINI_AVAILABLE and api_key and len(api_key) > 30:
        try:
            result['test_response'] = gemini_generate_text("Say 'Hello' in one word", api_key=api_key, model_name=model_name)
            result['status'] = 'success'
        except Exception as e:
            result['error'] = str(e)
            result['status'] = 'failed'
    else:
        result['status'] = 'not_configured'
    
    return jsonify(result)

