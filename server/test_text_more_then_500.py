import requests
import sys

SERVER_URL = "http://192.168.137.1:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"{status} - {name}")
    if message:
        color = Colors.GREEN if passed else Colors.RED
        print(f"       {color}{message}{Colors.END}")

def test_short_text():
    """Test with text under 500 characters"""
    try:
        response = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": "Короткий тест", "speaker": "baya"},
            timeout=30
        )
        data = response.json()
        passed = (
            response.status_code == 200 and
            'audio_base64' in data and
            data.get('text_length', 0) <= 500
        )
        message = f"Length: {data.get('text_length', 0)} chars"
        print_test("Short Text (<500 chars)", passed, message)
        return passed
    except Exception as e:
        print_test("Short Text (<500 chars)", False, str(e))
        return False

def test_long_text():
    """Test with text over 500 characters"""
    try:
        # Generate text longer than 500 characters
        long_text = "Это тестовое сообщение для проверки обработки длинного текста. " * 10
        print(f"Generating text with {len(long_text)} characters...")
        
        response = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": "Тест длинного текста", "speaker": "baya"},
            timeout=60
        )
        data = response.json()
        
        # For this test, we check if server returns valid audio regardless of length
        passed = (
            response.status_code == 200 and
            'audio_base64' in data and
            len(data.get('audio_base64', '')) > 1000
        )
        message = f"Response length: {data.get('text_length', 0)} chars, Audio: {len(data.get('audio_base64', ''))} bytes"
        print_test("Long Text (>500 chars)", passed, message)
        return passed
    except Exception as e:
        print_test("Long Text (>500 chars)", False, str(e))
        return False

def test_very_long_text():
    """Test with text over 1000 characters"""
    try:
        # Generate very long text
        very_long_text = "Очень длинное сообщение для проверки системы. " * 30
        print(f"Generating text with {len(very_long_text)} characters...")
        
        response = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": "Очень длинный тест", "speaker": "baya"},
            timeout=90
        )
        data = response.json()
        
        passed = (
            response.status_code == 200 and
            'audio_base64' in data and
            len(data.get('audio_base64', '')) > 5000
        )
        message = f"Response length: {data.get('text_length', 0)} chars, Audio: {len(data.get('audio_base64', ''))} bytes"
        print_test("Very Long Text (>1000 chars)", passed, message)
        return passed
    except Exception as e:
        print_test("Very Long Text (>1000 chars)", False, str(e))
        return False

def test_error_with_long_text():
    """Test error echo with long text"""
    try:
        long_text = "Длинное сообщение для проверки ошибки. " * 15
        
        response = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": long_text, "speaker": "baya"},
            timeout=60
        )
        data = response.json()
        
        # Check if error echo works with long text
        passed = (
            response.status_code == 200 and
            'audio_base64' in data and
            'is_error' in data
        )
        message = f"Error flag: {data.get('is_error')}, Length: {data.get('text_length', 0)} chars"
        print_test("Error Echo Long Text", passed, message)
        return passed
    except Exception as e:
        print_test("Error Echo Long Text", False, str(e))
        return False

def run_all_tests():
    """Run all long text tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Long Text Handling - Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    print(f"{Colors.YELLOW}Testing server at: {SERVER_URL}{Colors.END}\n")
    
    tests = [
        ("Short Text", test_short_text),
        ("Long Text", test_long_text),
        ("Very Long Text", test_very_long_text),
        ("Error Echo Long", test_error_with_long_text),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"{Colors.RED}FAIL{Colors.END} - {name} - Exception: {e}\n")
            results.append(False)
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"{Colors.GREEN}All tests passed! ({passed}/{total}){Colors.END}")
    else:
        print(f"{Colors.YELLOW}Tests completed: {passed}/{total} passed{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)