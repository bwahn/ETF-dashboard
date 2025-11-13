import requests
import time
import hashlib
import json
import jwt
import uuid
from urllib.parse import urlencode

# --- API 키 설정 ---
API_KEY = ""
API_SECRET = ""
BASE_URL = "https://api.bithumb.com"
# v2.1.5
# https://apidocs.bithumb.com/v2.1.5/reference/%EC%A3%BC%EB%AC%B8%ED%95%98%EA%B8%B0


def create_jwt_token(request_body=None):
    """빗썸 API v2.1.5 JWT 토큰 생성"""
    payload = {
        "access_key": API_KEY,
        "nonce": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000)
    }
    
    if request_body:
        if isinstance(request_body, dict):
            query_string = urlencode(request_body)
        else:
            query_string = request_body
            
        query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()
        payload["query_hash"] = query_hash
        payload["query_hash_alg"] = "SHA512"
    
    token = jwt.encode(payload, API_SECRET, algorithm='HS256')
    return f"Bearer {token}"

def get_current_usdt_price():
    """USDT 현재가 조회"""
    try:
        url = f"{BASE_URL}/public/ticker/USDT_KRW"
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") == "0000":
            ticker_data = data['data']
            current_price = int(float(ticker_data['closing_price']))
            buy_price = int(float(ticker_data.get('buy_price', current_price)))  # 매수 호가
            sell_price = int(float(ticker_data.get('sell_price', current_price)))  # 매도 호가
            
            return {
                'current': current_price,
                'buy': buy_price,
                'sell': sell_price
            }
        return None
    except Exception as e:
        print(f"가격 조회 오류: {e}")
        return None

def get_account_balance():
    """계좌 잔고 조회"""
    url = f"{BASE_URL}/v1/accounts"
    
    authorization_token = create_jwt_token()
    headers = {
        "Authorization": authorization_token,
        "accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"잔고 조회 오류: {e}")
        return None



def sell_usdt(volume, price):
    """USDT 지정가 매도"""
    url = f"{BASE_URL}/v1/orders"
    
    request_body = {
        "market": "KRW-USDT",
        "side": "ask",  # ask = 매도
        "volume": str(volume),
        "price": str(price),
        "ord_type": "limit"
    }
    
    authorization_token = create_jwt_token(request_body)
    headers = {
        "Authorization": authorization_token,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=request_body)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"매도 실패: {response.text}")
            return None
    except Exception as e:
        print(f"매도 오류: {e}")
        return None

def sell_usdt_market(volume):
    """USDT 시장가 매도 (즉시 체결)"""
    url = f"{BASE_URL}/v1/orders"
    
    request_body = {
        "market": "KRW-USDT",
        "side": "ask",  # ask = 매도
        "volume": str(volume),
        "ord_type": "market"  # 시장가 매도
    }
    
    authorization_token = create_jwt_token(request_body)
    headers = {
        "Authorization": authorization_token,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=request_body)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"시장가 매도 실패: {response.text}")
            return None
    except Exception as e:
        print(f"시장가 매도 오류: {e}")
        return None

def main():
    """테더 모두 매도 실행"""
    print("=== 빗썸 USDT 전량 매도 프로그램 ===\n")
    
    # 1. 현재가 조회
    print("1. USDT 현재가 조회 중...")
    price_info = get_current_usdt_price()
    if not price_info:
        print("❌ 가격 조회 실패")
        return
    
    print(f"   ✅ USDT 현재가: {price_info['current']:,} KRW")
    print(f"   📈 매수 호가 (살 수 있는 가격): {price_info['buy']:,} KRW")
    print(f"   📉 매도 호가 (팔 수 있는 가격): {price_info['sell']:,} KRW")
    
    # 2. 잔고 조회
    print("\n2. 계좌 잔고 조회 중...")
    accounts = get_account_balance()
    if not accounts:
        print("❌ 잔고 조회 실패")
        return
    
    # USDT 계좌 찾기
    usdt_balance = 0
    for account in accounts:
        if account.get('currency') == 'USDT':
            usdt_balance = float(account.get('balance', 0))
            break
    
    if usdt_balance <= 0:
        print("❌ 매도할 USDT가 없습니다.")
        return
    
    print(f"   ✅ 보유 USDT: {usdt_balance:.8f} USDT")
    
    # 3. 시장가 전체 매도 계획
    total_usdt = usdt_balance
    
    print(f"\n3. 시장가 전체 매도 계획:")
    print(f"   - 매도할 수량: {total_usdt:.8f} USDT (보유 전체)")
    print(f"   - 매도 방식: 시장가 (즉시 체결)")
    print(f"   - 예상 수익: 현재 시세에 따라 결정")
    
    print("   자동으로 시장가 매도를 진행합니다...")
    
    # 4. 실제 시장가 전체 매도 실행
    print(f"\n4. 시장가 전체 매도 주문 실행 중...")
    result = sell_usdt_market(total_usdt)
    
    if result:
        print(f"✅ 시장가 매도 주문 성공!")
        print(f"📋 주문 정보:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print(f"\n📊 매도 주문 결과:")
        print(f"   - 주문 UUID: {result.get('uuid', 'N/A')}")
        print(f"   - 주문 상태: {result.get('state', 'N/A')}")
        print(f"   - 매도 수량: {result.get('volume', 'N/A')} USDT")
        print(f"   - 매도 가격: {result.get('price', 'N/A')} KRW")
        print(f"   - 생성 시간: {result.get('created_at', 'N/A')}")
        
        print(f"\n🎉 축하합니다! USDT 시장가 매도 주문이 완료되었습니다!")
        print(f"📈 시장가 주문이므로 즉시 체결되었을 가능성이 높습니다.")
        print(f"📊 빗썸에서 체결 결과를 확인하세요.")
        
    else:
        print(f"❌ 시장가 매도 주문 실패")

if __name__ == "__main__":
    main()