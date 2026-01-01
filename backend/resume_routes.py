import os
import re
import json
import PyPDF2
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, User, Student
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

resume_bp = Blueprint('resume', __name__)

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads' / 'resumes'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

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
        
        # Save file
        filename = secure_filename(f"resume_{student.id}_{file.filename}")
        filepath = UPLOAD_FOLDER / filename
        file.save(filepath)
        
        # Parse resume if PDF
        parsed_data = {}
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
            print(f"Extracted text length: {len(text)}")  # Debug
            parsed_data = parse_resume_data(text)
            print(f"Parsed data: {parsed_data}")  # Debug
        
        # Update student record
        student.resume_url = f"/uploads/resumes/{filename}"
        db.session.commit()
        
        return jsonify({
            'message': 'Resume uploaded successfully',
            'resume_url': student.resume_url,
            'parsed_data': parsed_data
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
        
        # Construct file path
        filename = student.resume_url.split('/')[-1]
        filepath = UPLOAD_FOLDER / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Resume file not found'}), 404
        
        # Parse resume
        parsed_data = {}
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(filepath)
            parsed_data = parse_resume_data(text)
        
        return jsonify({
            'parsed_data': parsed_data
        }), 200
        
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
        
        # Construct file path
        filename = student.resume_url.split('/')[-1]
        filepath = UPLOAD_FOLDER / filename
        
        # Delete file if exists
        if filepath.exists():
            filepath.unlink()
        
        # Update student record
        student.resume_url = None
        student.ats_score = None
        student.ats_feedback = None
        student.ats_calculated_at = None
        db.session.commit()
        
        return jsonify({
            'message': 'Resume deleted successfully'
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
        genai.configure(api_key=api_key)
        model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        model = genai.GenerativeModel(model_name)
        
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
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
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
        return None, str(e)


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
        genai.configure(api_key=api_key)
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        model = genai.GenerativeModel(model_name)
        
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
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
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
        return None, str(e)


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
        
        # Construct file path
        filename = student.resume_url.split('/')[-1]
        filepath = UPLOAD_FOLDER / filename
        
        if not filepath.exists():
            return jsonify({'error': 'Resume file not found'}), 404
        
        # Extract text from PDF
        resume_text = ""
        if filename.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(filepath)
        
        if not resume_text:
            return jsonify({'error': 'Could not extract text from resume'}), 400
        
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
            
            filename = student.resume_url.split('/')[-1]
            filepath = UPLOAD_FOLDER / filename
            
            if not filepath.exists():
                return jsonify({'error': 'Profile resume file not found'}), 404
            
            if filename.lower().endswith('.pdf'):
                resume_text = extract_text_from_pdf(filepath)
        
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
        'api_key_configured': bool(api_key and api_key != 'YOUR_GEMINI_API_KEY_HERE' and len(api_key) > 30),
        'api_key_length': len(api_key) if api_key else 0,
        'api_key_preview': api_key[:10] + '...' if api_key and len(api_key) > 10 else 'N/A',
        'model_name': model_name,
        'env_path': str(env_path),
        'env_exists': env_path.exists()
    }
    
    if GEMINI_AVAILABLE and api_key and len(api_key) > 30:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'Hello' in one word")
            result['test_response'] = response.text
            result['status'] = 'success'
        except Exception as e:
            result['error'] = str(e)
            result['status'] = 'failed'
    else:
        result['status'] = 'not_configured'
    
    return jsonify(result)

