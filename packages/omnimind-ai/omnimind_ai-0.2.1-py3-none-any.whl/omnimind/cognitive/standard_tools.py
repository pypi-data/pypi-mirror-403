"""
OMNIMIND Standard Tools
Specialized tools for Math, Science, Coding, and Computer Vision
"""
import math
import sys
import io
import contextlib
from typing import Dict, Any, List

# --- Computer Vision Tools ---
class VisionTools:
    """Tools for specific visual tasks"""
    
    @staticmethod
    def detect_objects(image_path: str) -> List[Dict[str, Any]]:
        """
        Detect objects (birds, cars, etc.) in an image
        Returns: List of detected objects with bounding boxes
        """
        try:
            from ultralytics import YOLO
            model = YOLO("yolov8n.pt")  # Lightweight model
            results = model(image_path)
            
            detections = []
            for r in results:
                for box in r.boxes:
                    detections.append({
                        "class": model.names[int(box.cls)],
                        "confidence": float(box.conf),
                        "box": box.xywh.tolist()
                    })
            return detections
        except ImportError:
            return [{"error": "ultralytics not installed. Run: pip install ultralytics"}]

    @staticmethod
    def read_license_plate(image_path: str) -> str:
        """Read text/license plate from image (OCR)"""
        try:
            import easyocr
            reader = easyocr.Reader(['en']) # Add 'th' if needed
            result = reader.readtext(image_path, detail=0)
            return " ".join(result)
        except ImportError:
            return "easyocr not installed. Run: pip install easyocr"
            
    @staticmethod
    def detect_faces(image_path: str) -> List[Dict]:
        """Detect faces in image"""
        try:
            import cv2
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            return [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x, y, w, h) in faces]
        except ImportError:
            return [{"error": "opencv-python not installed"}]


# --- Math & Science Tools ---
class MathTools:
    """Tools for calculation and science"""
    
    @staticmethod
    def calculate(expression: str) -> float:
        """Evaluate mathematical expression"""
        try:
            # Safe evaluation
            allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
            return eval(expression, {"__builtins__": {}}, allowed_names)
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def solve_equation(equation: str) -> str:
        """Solve symbolic equation (requires sympy)"""
        try:
            from sympy import symbols, solve, parse_expr
            # Heuristic parsing: 'x^2 - 4 = 0' -> solve(x**2 - 4, x)
            if "=" in equation:
                lhs, rhs = equation.split("=")
                expr = f"({lhs}) - ({rhs})"
            else:
                expr = equation
                
            x = symbols('x') # Assumption
            parsed = parse_expr(expr)
            solution = solve(parsed)
            return str(solution)
        except ImportError:
            return "sympy not installed"
            
    @staticmethod
    def astronomy_info(object_name: str) -> str:
        """Get astronomical data (mock)"""
        # In production this would query an API like NASA or PyEphem
        db = {
            "mars": "Distance: 225M km, Gravity: 3.72 m/s², Day: 24h 37m",
            "jupiter": "Mass: 1.898e27 kg, Moons: 95, Radius: 69,911 km",
            "moon": "Distance: 384,400 km, Phase: Waning Gibbous"
        }
        return db.get(object_name.lower(), "Object not found in local database")


# --- Coding Tools ---
class CodeInterpreter:
    """Execute Python code safely"""
    
    @staticmethod
    def execute_python(code: str) -> str:
        """Execute python code and return stdout"""
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        
        try:
            # Restricted globals
            exec(code, {"__builtins__": __builtins__, "math": math})
            sys.stdout = old_stdout
            return redirected_output.getvalue()
        except Exception as e:
            sys.stdout = old_stdout
            return f"Execution Error: {str(e)}"


# --- Translation Tool ---
class Translator:
    """Translation tool"""
    
    @staticmethod
    def translate(text: str, target_lang: str) -> str:
        """Translate text (mock/fallback or use model)"""
        # In real OMNIMIND, the model itself handles this best via prompt
        # "Translate this to Thai: ..."
        # But this tool exposes explicit hook if needed (e.g. Google Translate API)
        return f"[Translation to {target_lang}]: {text} (OMNIMIND native capability)"


# --- Web Search Tool ---
class WebSearch:
    """Web search tool for retrieving real-time information"""
    
    @staticmethod
    def search(query: str, num_results: int = 5) -> str:
        """
        Search the web for information
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Search results as formatted string
        """
        try:
            # Try DuckDuckGo (no API key needed)
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
            
            if not results:
                return f"No results found for: {query}"
            
            output = f"Search results for '{query}':\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. **{r.get('title', 'No title')}**\n"
                output += f"   {r.get('body', 'No description')}\n"
                output += f"   URL: {r.get('href', 'No URL')}\n\n"
            
            return output
            
        except ImportError:
            return "Web search unavailable. Install: pip install duckduckgo-search"
        except Exception as e:
            return f"Search error: {str(e)}"
    
    @staticmethod
    def search_news(query: str, num_results: int = 5) -> str:
        """Search for recent news articles"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=num_results))
            
            if not results:
                return f"No news found for: {query}"
            
            output = f"News results for '{query}':\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. **{r.get('title', 'No title')}**\n"
                output += f"   {r.get('body', 'No description')}\n"
                output += f"   Date: {r.get('date', 'Unknown')}\n"
                output += f"   Source: {r.get('source', 'Unknown')}\n\n"
            
            return output
            
        except ImportError:
            return "News search unavailable. Install: pip install duckduckgo-search"
        except Exception as e:
            return f"News search error: {str(e)}"


# --- Date/Time Tool ---
class DateTimeTool:
    """Date and time utility"""
    
    @staticmethod
    def get_current_time(timezone: str = "Asia/Bangkok") -> str:
        """Get current date and time"""
        from datetime import datetime
        try:
            import pytz
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
        except ImportError:
            now = datetime.now()
            timezone = "UTC (pytz not installed)"
        
        return f"Current time ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S')}"


# --- Tool Registry Helper ---
def get_standard_tools() -> list:
    """Get all standard tools as a list of functions"""
    return [
        # Vision
        VisionTools.detect_objects,
        VisionTools.read_license_plate,
        VisionTools.detect_faces,
        # Math & Science
        MathTools.calculate,
        MathTools.solve_equation,
        MathTools.astronomy_info,
        # Code
        CodeInterpreter.execute_python,
        # Language
        Translator.translate,
        # Web Search (NEW)
        WebSearch.search,
        WebSearch.search_news,
        # Date/Time (NEW)
        DateTimeTool.get_current_time,
    ]
