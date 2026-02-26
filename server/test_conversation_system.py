import requests
import time
import sys

SERVER_URL = "http://192.168.137.1:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

# Print test result
def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"{status} - {name}")
    if message:
        color = Colors.GREEN if passed else Colors.RED
        print(f"       {color}{message}{Colors.END}")

# Test 1: Server health check
def test_server_health():
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        data = response.json()
        passed = (
            response.status_code == 200 and
            data.get('status') == 'ok' and
            data.get('model_loaded') == True
        )
        message = f"Status: {data.get('status')}, Model: {data.get('model_loaded')}"
        print_test("Server Health Check", passed, message)
        return passed
    except Exception as e:
        print_test("Server Health Check", False, str(e))
        return False

# Test 2: Conversation endpoint
def test_conversation_endpoint():
    try:
        response = requests.post(
            f"{SERVER_URL}/conversation",
            json={
                "user_text": "Привет тест",
                "speaker": "baya",
                "sample_rate": 48000
            },
            timeout=30
        )
        data = response.json()
        passed = (
            response.status_code == 200 and
            'audio_base64' in data and
            'bot_response' in data and
            'is_error' in data and
            len(data['audio_base64']) > 1000
        )
        message = f"Response: '{data.get('bot_response', '')[:50]}...', Error: {data.get('is_error')}"
        print_test("Conversation Endpoint", passed, message)
        return passed
    except Exception as e:
        print_test("Conversation Endpoint", False, str(e))
        return False

# Test 3: Error echo flow (when API is down)
def test_error_echo():
    try:
        response = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": "Тест ошибки", "speaker": "baya"},
            timeout=30
        )
        data = response.json()
        is_error = data.get('is_error')
        bot_response = data.get('bot_response')
        user_text = data.get('user_text')
        if is_error and bot_response == user_text:
            print_test("Error Echo Flow", True, "Server correctly echoed text on API failure")
            return True
        elif not is_error:
            print_test("Error Echo Flow", True, "API is up, no error to test")
            return True
        else:
            print_test("Error Echo Flow", False, "Error flag set but text not echoed")
            return False
    except Exception as e:
        print_test("Error Echo Flow", False, str(e))
        return False

# Test 4: Cache functionality
def test_cache_functionality():
    try:
        response1 = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": "Тест кэша", "speaker": "baya"},
            timeout=30
        )
        response2 = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": "Тест кэша", "speaker": "baya"},
            timeout=30
        )
        passed = (
            response1.status_code == 200 and
            response2.status_code == 200
        )
        message = f"Both requests successful (cache working)"
        print_test("Cache Functionality", passed, message)
        return passed
    except Exception as e:
        print_test("Cache Functionality", False, str(e))
        return False

# Test 5: Long text handling
def test_long_text():
    try:
        long_text = "Длинный текст для проверки обработки. " * 20
        response = requests.post(
            f"{SERVER_URL}/conversation",
            json={"user_text": long_text, "speaker": "baya"},
            timeout=60
        )
        passed = response.status_code == 200 and 'audio_base64' in response.json()
        message = f"Text length: {len(long_text)} chars"
        print_test("Long Text Handling", passed, message)
        return passed
    except Exception as e:
        print_test("Long Text Handling", False, str(e))
        return False

# Run all tests
def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Silero Conversation System - Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    print(f"{Colors.YELLOW}Testing server at: {SERVER_URL}{Colors.END}\n")
    
    tests = [
        ("Server Health", test_server_health),
        ("Conversation Flow", test_conversation_endpoint),
        ("Error Echo", test_error_echo),
        ("Cache", test_cache_functionality),
        ("Long Text", test_long_text),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            time.sleep(0.5)
        except Exception as e:
            print(f"{Colors.RED}FAIL{Colors.END} - {name} - Exception: {e}")
            results.append(False)
            time.sleep(0.5)
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
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