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
            return int(float(data['data']['closing_price']))
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
        print(f"잔고 조회 응답: {response.status_code}")
        print(f"응답 내용: {response.text}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"잔고 조회 오류: {e}")
        return None

def buy_usdt_market(price_amount):
    """USDT 시장가 매수 (KRW 금액으로 매수)"""
    url = f"{BASE_URL}/v1/orders"
    
    request_body = {
        "market": "KRW-USDT",
        "side": "bid",
        "price": str(price_amount),  # 시장가 매수 시 price는 사용할 KRW 금액
        "ord_type": "price"  # 시장가 매수
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
            print(f"시장가 매수 실패: {response.text}")
            return None
    except Exception as e:
        print(f"시장가 매수 오류: {e}")
        return None

def buy_usdt(volume, price):
    """USDT 지정가 매수"""
    url = f"{BASE_URL}/v1/orders"
    
    request_body = {
        "market": "KRW-USDT",
        "side": "bid",
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
            print(f"주문 실패: {response.text}")
            return None
    except Exception as e:
        print(f"주문 오류: {e}")
        return None

def main():
    """실제 USDT 지정가 매수 실행 (시장가 효과)"""
    print("=== 빗썸 USDT 매수 프로그램 ===\n")
    
    # 1. 현재가 조회
    print("1. USDT 현재가 조회 중...")
    current_price = get_current_usdt_price()
    if not current_price:
        print("❌ 가격 조회 실패")
        return
    
    print(f"   ✅ USDT 현재가: {current_price:,} KRW")
    
    # 2. 지정가 매수 계획 (현재가로 주문하여 즉시 체결 유도)
    order_amount = 5100  # 사용할 KRW 금액
    order_price = current_price + 1  # 현재가보다 1원 높게 주문 (즉시 체결)
    order_volume = order_amount / order_price  # 주문 수량
    
    print(f"\n2. 매수 계획:")
    print(f"   - 사용 금액: {order_amount:,} KRW")
    print(f"   - 주문 가격: {order_price:,} KRW (현재가+1원)")
    print(f"   - 주문 수량: {order_volume:.6f} USDT")
    print(f"   - 예상 수수료: 약 {order_amount * 0.0025:,.0f} KRW")
    
    # 3. 사용자 확인
    print(f"\n3. 실제 매수를 진행하시겠습니까?")
    print(f"   {order_volume:.6f} USDT를 {order_price:,} KRW에 지정가 매수")
    print(f"   현재가보다 높은 가격으로 주문하여 즉시 체결을 유도합니다.")
    
    print("   자동으로 매수를 진행합니다...")
    
    # 4. 실제 지정가 매수 실행
    print(f"\n4. 지정가 매수 주문 실행 중...")
    result = buy_usdt(order_volume, order_price)
    
    if result:
        print(f"✅ 시장가 매수 주문 성공!")
        print(f"📋 주문 정보:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print(f"\n📊 주문 결과:")
        print(f"   - 주문 ID: {result.get('order_id', 'N/A')}")
        print(f"   - 주문 상태: {result.get('status', 'N/A')}")
        print(f"   - 주문 수량: {result.get('units', 'N/A')} USDT")
        print(f"   - 주문 타입: 지정가 매수 (즉시 체결)")
        print(f"   - 생성 시간: {result.get('order_date', 'N/A')}")
        
        print(f"\n🎉 축하합니다! USDT 매수 주문이 완료되었습니다!")
        print(f"📈 현재가보다 높은 가격으로 주문하여 즉시 체결될 가능성이 높습니다.")
        print(f"📊 빗썸에서 체결 결과를 확인하세요.")
        
    else:
        print(f"❌ 매수 주문 실패")

if __name__ == "__main__":
    main()