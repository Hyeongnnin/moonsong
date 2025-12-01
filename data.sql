SELECT * FROM labor_employee;
INSERT INTO labor_employee (
    workplace_name,
    workplace_address,
    workplace_reg_no,
    industry,
    employment_type,
    start_date,
    hourly_rate,
    weekly_hours,
    daily_hours,
    has_paid_weekly_holiday,      -- 여기 컬럼 이름은 뷰어에서 보이는 그대로 써줘
    is_severance_eligible,
    is_current,
    user_id
)
VALUES (
    '메가커피 강남점',        -- workplace_name
    '서울시 강남구',          -- workplace_address
    '000-00-00000',          -- workplace_reg_no (대충 사업자번호 느낌)
    '음식료',                 -- industry
    '알바',                   -- employment_type
    '2025-07-01',            -- start_date (YYYY-MM-DD)
    11000,                   -- hourly_rate
    20,                      -- weekly_hours
    0,                       -- daily_hours (필요하면 0으로 두고 나중에 계산)
    1,                       -- has_paid_weekly_ho: 1=주휴수당 있음, 0=없음
    0,                       -- is_severance_eligible: 1=퇴직금 대상, 0=아님
    1,                       -- is_current: 1=현재 재직, 0=퇴사
    1                        -- user_id: 지금 로그인 유저의 id (보통 1일 가능성 큼)
);

