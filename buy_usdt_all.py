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

def create_jwt_token(request_body=None):
    """JWT 토큰 생성"""
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
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"잔고 조회 오류: {e}")
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
    """실제 USDT 1개 매수 실행"""
    print("=== 빗썸 USDT 1개 실제 매수 프로그램 ===\n")
    
    # 1. 현재가 조회
    print("1. USDT 현재가 조회 중...")
    current_price = get_current_usdt_price()
    if not current_price:
        print("❌ 가격 조회 실패")
        return
    
    print(f"   ✅ USDT 현재가: {current_price:,} KRW")
    
    # 2. 잔고 조회
    print("\n2. 계좌 잔고 조회 중...")
    accounts = get_account_balance()
    if not accounts:
        print("❌ 잔고 조회 실패")
        return
    
    # KRW 계좌 찾기
    krw_balance = 0
    for account in accounts:
        if account.get('currency') == 'KRW':
            krw_balance = float(account.get('balance', 0))
            break
    
    print(f"   ✅ 사용 가능한 KRW: {krw_balance:,} KRW")
    
    # 3. 매수 계획
    min_order_amount = 5100  # 빗썸 최소 주문 금액보다 여유있게
    target_price = current_price  # 현재가로 주문 (체결 확률 높임)
    target_volume = min_order_amount / target_price  # 최소 주문 금액에 맞는 수량
    required_krw = target_volume * target_price
    
    print(f"\n3. 매수 계획:")
    print(f"   - 주문 금액: {min_order_amount:,} KRW (최소 주문 금액 5,000원 이상)")
    print(f"   - 주문 가격: {target_price:,} KRW (현재가)")
    print(f"   - 매수 수량: {target_volume:.6f} USDT")
    print(f"   - 총 금액: {required_krw:,} KRW")
    
    if krw_balance < required_krw:
        print(f"❌ KRW 잔고 부족 (보유: {krw_balance:,}, 필요: {required_krw:,})")
        return
    
    print(f"   ✅ 매수 가능!")
    
    # 4. 사용자 확인
    print(f"\n4. 실제 매수를 진행하시겠습니까?")
    print(f"   {target_volume:.6f} USDT를 {target_price:,} KRW에 지정가 매수")
    print(f"   총 주문 금액: {required_krw:,} KRW")
    print(f"   예상 수수료: 약 {required_krw * 0.0025:,.0f} KRW")
    
    confirm = input("   진행하시겠습니까? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("   매수를 취소했습니다.")
        return
    
    # 5. 실제 매수 실행
    print(f"\n5. 매수 주문 실행 중...")
    result = buy_usdt(target_volume, target_price)
    
    if result:
        print(f"✅ 매수 주문 성공!")
        print(f"📋 주문 정보:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print(f"\n📊 주문 결과:")
        print(f"   - 주문 UUID: {result.get('uuid', 'N/A')}")
        print(f"   - 주문 상태: {result.get('state', 'N/A')}")
        print(f"   - 주문 수량: {result.get('volume', 'N/A')} USDT")
        print(f"   - 주문 가격: {result.get('price', 'N/A')} KRW")
        print(f"   - 생성 시간: {result.get('created_at', 'N/A')}")
        
        print(f"\n🎉 축하합니다! USDT 매수 주문이 완료되었습니다!")
        print(f"📈 빗썸에서 주문 상태를 확인하세요.")
        
    else:
        print(f"❌ 매수 주문 실패")

if __name__ == "__main__":
    main()
