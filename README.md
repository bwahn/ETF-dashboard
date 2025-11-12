# ETF 대시보드 Google 시트 가이드

## 개요

ETF 배당 흐름을 추적하고 한눈에 지표를 볼 수 있는 Google 시트를 만드는 방법을 정리했습니다. 전체 문서는 `Dashboard` 시트 1개와 티커별 시트 4개(`HOOY`, `NVDY`, `PLTY`, `WPAY`)로 구성되며, `GOOGLEFINANCE` 함수를 활용해 가격과 배당 정보를 자동으로 갱신합니다.

---

## 1. 시트 구성

- 첫 화면용 `Dashboard` 시트를 만듭니다.
- ETF마다 개별 시트(`HOOY`, `NVDY`, `PLTY`, `WPAY`)를 추가합니다.
- `Dashboard`의 예: `A2:A5`에 티커 목록을 적고, 이 범위를 `Tickers`라는 이름 범위로 지정합니다.

---

## 2. 티커별 시트(배당 히스토리)

아래 설정을 각 ETF 시트에 반복합니다.

1. 1행에 헤더를 추가합니다: `Date`, `Dividend`, `Notes`, `Year`, `Month`, `Month Key`, `Running Total`.
2. `A2` 셀에 다음 배열 수식을 입력합니다.

```text
=ARRAYFORMULA(
  LET(
    raw, GOOGLEFINANCE("HOOY","dividend", DATE(2018,1,1), TODAY()),
    cleaned, IF(ROW(raw)=1, {"Date","Dividend"}, raw),
    FILTER(cleaned, INDEX(cleaned,,2) <> "")
  )
)
```

`"HOOY"` 부분을 해당 시트의 티커로 바꿔 입력하고, 더 긴 이력을 원하면 시작 날짜를 조정하세요.

3. 보조 열을 채우는 수식은 아래와 같습니다.

- `Year`(D열): `=ARRAYFORMULA(IF(A2:A="",,YEAR(A2:A)))`
- `Month`(E열): `=ARRAYFORMULA(IF(A2:A="",,TEXT(A2:A,"mmm")))`
- `Month Key`(F열): `=ARRAYFORMULA(IF(A2:A="",,TEXT(A2:A,"yyyy-mm")))`
- `Running Total`(G열): `=ARRAYFORMULA(IF(B2:B="",,MMULT(--(ROW(B2:B)>=TRANSPOSE(ROW(B2:B))),B2:B)))`

4. 최신 배당을 강조하려면 조건부 서식을 지정합니다.

- 범위: `A2:B`
- 사용자 지정 수식: `=A2=MAX($A:$A)` → 연한 배경색 등으로 강조

---

## 3. 대시보드 콘텐츠

### 3.1 티커 선택기

- 예: `B1` 셀을 선택한 뒤 데이터 유효성 검사 → 범위에서 목록 → `=Tickers`를 지정합니다.
- 왼쪽 셀(`A1`)에는 `Selected Ticker`와 같이 라벨을 넣어줍니다.

### 3.2 KPI 카드

선택된 티커 셀 `$B$1`을 참조하는 `GOOGLEFINANCE` 수식을 활용합니다. 예시는 다음과 같습니다.

| 지표               | 추천 셀 | 수식                                                |
| ------------------ | ------- | --------------------------------------------------- |
| Last Price         | `B3`    | `=IF($B$1="",,GOOGLEFINANCE($B$1,"price"))`         |
| Daily Change %     | `B4`    | `=IF($B$1="",,GOOGLEFINANCE($B$1,"changepct")/100)` |
| Distribution Yield | `B5`    | `=IF($B$1="",,GOOGLEFINANCE($B$1,"yield"))`         |
| 52w High           | `B6`    | `=IF($B$1="",,GOOGLEFINANCE($B$1,"high52"))`        |

카드 형태로 보이도록 테두리, 글꼴 굵게, 숫자 서식을 적용합니다. Google Finance는 최대 20분 지연될 수 있다는 안내 문구도 함께 적어두면 좋습니다.

### 3.3 최신 배당 스냅샷

- 티커 시트에서 가장 최근 배당을 불러오는 블록을 만듭니다(예: `E3`부터).

```text
=LET(
  tab, INDIRECT($B$1&"!A:G"),
  data, FILTER(tab, INDEX(tab,,2) <> ""),
  latest, INDEX(data, ROWS(data), ),
  {"Last Dividend Date","Amount","Running Total";
   INDEX(latest,1), INDEX(latest,2), INDEX(latest,7)}
)
```

- 출력 범위를 작은 표 형태로 꾸미면 가독성이 좋아집니다.

### 3.4 월별 배당 합계

전체 ETF의 배당을 월 단위로 합산해 대시보드 차트의 데이터 원본으로 사용합니다.

1. `Dashboard`에서 예: `A10` 셀에 다음 수식을 입력합니다.

```text
=LET(
  inflow, {
    FILTER({HOOY!F2:G, ARRAYFORMULA(IF(HOOY!B2:B="",,HOOY!B2:B)), ARRAYFORMULA(IF(HOOY!B2:B="",,"HOOY"))}, HOOY!B2:B<>"");
    FILTER({NVDY!F2:G, ARRAYFORMULA(IF(NVDY!B2:B="",,NVDY!B2:B)), ARRAYFORMULA(IF(NVDY!B2:B="",,"NVDY"))}, NVDY!B2:B<>"");
    FILTER({PLTY!F2:G, ARRAYFORMULA(IF(PLTY!B2:B="",,PLTY!B2:B)), ARRAYFORMULA(IF(PLTY!B2:B="",,"PLTY"))}, PLTY!B2:B<>"");
    FILTER({WPAY!F2:G, ARRAYFORMULA(IF(WPAY!B2:B="",,WPAY!B2:B)), ARRAYFORMULA(IF(WPAY!B2:B="",,"WPAY"))}, WPAY!B2:B<>"")
  },
  QUERY(
    inflow,
    "select Col1, sum(Col3) where Col3 is not null group by Col1 label sum(Col3) 'Dividends'",
    0
  )
)
```

이 수식은 `Month Key`와 `Dividends` 2열 표를 만듭니다. 원하면 `B`열 옆에 `Rolling 12M` 열을 추가해 누적 합계를 표시할 수 있습니다: `=ARRAYFORMULA(IF(B11:B="",,MMULT(--(ROW(B11:B)>=TRANSPOSE(ROW(B11:B))),B11:B)))`. 2. 선택한 티커만 월별로 보고 싶다면 예: `E10`에 다음 수식을 넣습니다.

```text
=LET(
  tab, INDIRECT($B$1&"!F2:G"),
  data, FILTER(tab, INDEX(tab,,2) <> ""),
  QUERY(data, "select Col1, sum(Col2) where Col2 is not null group by Col1 label sum(Col2) 'Dividends'", 0)
)
```

### 3.5 대시보드 차트

- 월별 합계 표 범위(`A10:B`)를 선택합니다.
- 삽입 → 차트 → 콤보 차트를 고릅니다.
- 시리즈 구성:
  - 막대 시리즈: 월별 배당 합계
  - (선택) 선 시리즈: 12개월 이동합
- X축을 `Month Key`로 지정하고 표시 형식은 `MMM YYYY`로 설정하면 읽기 쉽습니다.

---

## 4. 부가 기능

- **이름 범위**: `SelectedTicker`, `TickerKPIs` 등 자주 참조하는 구역은 이름 범위로 관리하면 수식이 단순해집니다.
- **새로고침 안내**: `Dashboard`에 `GOOGLEFINANCE` 지연(약 20분)과 수동 새로고침(`Cmd+R`/`Ctrl+R`) 방법을 적어두세요.
- **수동 보정**: Google에서 제공하지 않는 배당은 각 티커 시트의 자동 영역 아래쪽에 직접 입력하고 `Notes` 열에 메모합니다.
- **시트 보호**: 수식이 들어간 영역은 보호하고, 사용자가 입력해야 할 부분만 잠금 해제해 실수로 지우는 일을 줄입니다.

---

## 5. 다음 단계

- 다른 ETF를 추가하려면 티커 시트를 복제한 뒤 `GOOGLEFINANCE` 수식의 심볼만 바꾸면 됩니다.
- 지표를 확장하고 싶다면 비용비율, 운용자산(AUM), NAV 등 추가 KPI 카드를 만들어 수동 입력하거나 외부 데이터로 채워보세요.
- 배당 공시나 수익률 변동에 맞춰 알림을 받으려면 Apps Script나 이메일 자동화 기능을 연동해볼 수 있습니다.
