import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

fake = Faker("en_IN")
random.seed(42)

DATA_DIR = Path(__file__).parent

# ── Customers (50) ──────────────────────────────────────────────────────────
customers = []
for i in range(50):
    customers.append({
        "id": f"CUST{1000 + i}",
        "name": fake.name(),
        "pan": (
            "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
            + str(random.randint(1000, 9999))
            + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        ),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "credit_score": random.randint(550, 850),
        "kyc_status": random.choices(
            ["verified", "pending", "expired"], weights=[0.8, 0.15, 0.05]
        )[0],
        "segment": random.choices(
            ["retail", "premium", "sme", "corporate"], weights=[0.5, 0.25, 0.15, 0.1]
        )[0],
        "annual_income": random.randint(300000, 5000000),
        "device_id": f"DEV{random.randint(1000, 9999)}",
        "address": fake.address().replace("\n", ", "),
        "created_at": str(fake.date_between(start_date="-5y", end_date="-1y")),
    })

# ── Accounts (120) ──────────────────────────────────────────────────────────
accounts = []
for i in range(120):
    customer = random.choice(customers)
    last_txn = fake.date_between(start_date="-12m", end_date="today")
    accounts.append({
        "id": f"ACC{2000 + i}",
        "customer_id": customer["id"],
        "type": random.choice(["savings", "current", "fd", "rd", "premium_savings"]),
        "balance": round(random.uniform(1000, 2000000), 2),
        "status": random.choices(
            ["active", "dormant", "closed", "frozen"], weights=[0.7, 0.15, 0.1, 0.05]
        )[0],
        "last_txn_date": str(last_txn),
        "branch": fake.city(),
        "ifsc": f"FNCR{random.randint(10000, 99999)}",
        "opened_date": str(fake.date_between(start_date="-5y", end_date="-6m")),
        "min_balance": random.choice([1000, 5000, 10000, 25000]),
    })

# ── Transactions ─────────────────────────────────────────────────────────────
transactions = []
for acc in accounts[:80]:
    for _ in range(random.randint(5, 20)):
        risk_score = round(random.uniform(0, 1), 3)
        txn_date = fake.date_time_between(start_date="-6m", end_date="now")
        transactions.append({
            "id": f"TXN{str(uuid.uuid4())[:8].upper()}",
            "account_id": acc["id"],
            "amount": round(random.uniform(100, 500000), 2),
            "timestamp": str(txn_date),
            "payee_id": f"PAY{random.randint(1000, 9999)}",
            "payee_name": fake.name(),
            "channel": random.choice(["upi", "neft", "imps", "atm", "pos", "netbanking"]),
            "risk_score": risk_score,
            "type": random.choice(["debit", "credit"]),
            "description": random.choice([
                "Online Shopping", "Bill Payment", "Transfer",
                "ATM Withdrawal", "Salary Credit", "EMI Debit",
                "Investment", "Insurance Premium",
            ]),
            "is_flagged": risk_score > 0.75,
        })

# ── Loans (40) ───────────────────────────────────────────────────────────────
loans = []
for i in range(40):
    customer = random.choice(customers)
    amount = random.choice([200000, 500000, 1000000, 2000000, 5000000])
    loans.append({
        "id": f"LOAN{3000 + i}",
        "customer_id": customer["id"],
        "type": random.choice(["home", "personal", "car", "education", "msme", "gold"]),
        "amount": amount,
        "outstanding": round(amount * random.uniform(0.1, 0.95), 2),
        "emi": round(amount * random.uniform(0.02, 0.05), 2),
        "interest_rate": round(random.uniform(7.5, 18.0), 2),
        "tenure_months": random.choice([12, 24, 36, 60, 84, 120, 180, 240]),
        "status": random.choices(
            ["active", "closed", "npa", "applied"], weights=[0.6, 0.25, 0.1, 0.05]
        )[0],
        "disbursed_date": str(fake.date_between(start_date="-4y", end_date="-1m")),
        "next_emi_date": str(fake.date_between(start_date="today", end_date="+31d")),
    })

# ── Products (15) ────────────────────────────────────────────────────────────
products = [
    {"id": "PROD001", "name": "Basic Savings Account", "category": "account",
     "min_balance": 1000, "eligibility_criteria": "age >= 18, kyc_verified", "interest_rate": 3.5},
    {"id": "PROD002", "name": "Premium Savings Account", "category": "account",
     "min_balance": 25000, "eligibility_criteria": "credit_score >= 700, kyc_verified", "interest_rate": 4.5},
    {"id": "PROD003", "name": "Current Account", "category": "account",
     "min_balance": 10000, "eligibility_criteria": "business_entity, kyc_verified", "interest_rate": 0},
    {"id": "PROD004", "name": "Home Loan", "category": "loan",
     "min_balance": 0, "eligibility_criteria": "credit_score >= 650, kyc_verified", "interest_rate": 8.5},
    {"id": "PROD005", "name": "Personal Loan", "category": "loan",
     "min_balance": 0, "eligibility_criteria": "credit_score >= 680", "interest_rate": 13.5},
    {"id": "PROD006", "name": "Car Loan", "category": "loan",
     "min_balance": 0, "eligibility_criteria": "credit_score >= 650", "interest_rate": 9.5},
    {"id": "PROD007", "name": "MSME Business Loan", "category": "loan",
     "min_balance": 0, "eligibility_criteria": "gst_registered, credit_score >= 620", "interest_rate": 11.5},
    {"id": "PROD008", "name": "Education Loan", "category": "loan",
     "min_balance": 0, "eligibility_criteria": "age <= 35, admission_proof", "interest_rate": 9.0},
    {"id": "PROD009", "name": "Fixed Deposit", "category": "investment",
     "min_balance": 5000, "eligibility_criteria": "existing_customer", "interest_rate": 7.2},
    {"id": "PROD010", "name": "Recurring Deposit", "category": "investment",
     "min_balance": 500, "eligibility_criteria": "existing_customer", "interest_rate": 6.8},
    {"id": "PROD011", "name": "Gold Loan", "category": "loan",
     "min_balance": 0, "eligibility_criteria": "gold_collateral, kyc_verified", "interest_rate": 10.5},
    {"id": "PROD012", "name": "Credit Card Classic", "category": "card",
     "min_balance": 0, "eligibility_criteria": "credit_score >= 700", "interest_rate": 36},
    {"id": "PROD013", "name": "Credit Card Premium", "category": "card",
     "min_balance": 0, "eligibility_criteria": "credit_score >= 750", "interest_rate": 36},
    {"id": "PROD014", "name": "Zero Balance Account", "category": "account",
     "min_balance": 0, "eligibility_criteria": "age >= 18, kyc_verified", "interest_rate": 3.0},
    {"id": "PROD015", "name": "NRI Savings Account", "category": "account",
     "min_balance": 10000, "eligibility_criteria": "nri_status", "interest_rate": 4.0},
]

# ── Regulation Rules (8) ─────────────────────────────────────────────────────
regulation_rules = [
    {"id": "REG001", "source": "RBI", "title": "Home Loan LTV Ratio",
     "description": "LTV must not exceed 90% for loans up to 30L, 80% for 30-75L, 75% above 75L",
     "effective_date": "2020-01-01", "applies_to": "home_loan"},
    {"id": "REG002", "source": "RBI", "title": "Personal Loan EMI Cap",
     "description": "Total EMI must not exceed 50% of net monthly income (FOIR <= 0.5)",
     "effective_date": "2019-06-01", "applies_to": "personal_loan"},
    {"id": "REG003", "source": "RBI", "title": "MSME Priority Sector Lending",
     "description": "MSME loans qualify for priority sector. Max 10Cr micro, 50Cr small",
     "effective_date": "2021-04-01", "applies_to": "msme_loan"},
    {"id": "REG004", "source": "RBI", "title": "KYC Mandatory",
     "description": "KYC re-verification required every 2 years for high-risk customers",
     "effective_date": "2023-01-01", "applies_to": "all_accounts"},
    {"id": "REG005", "source": "RBI", "title": "Fraud Reporting Window",
     "description": "Fraud above 1L must be reported within 1 week. Above 5Cr within 24 hours",
     "effective_date": "2020-07-01", "applies_to": "fraud_transactions"},
    {"id": "REG006", "source": "DPDP", "title": "Customer Data Privacy",
     "description": "Under DPDP Act 2023, financial data cannot be shared without consent",
     "effective_date": "2023-08-11", "applies_to": "all_data"},
    {"id": "REG007", "source": "RBI", "title": "Credit Card Interest Cap",
     "description": "Max interest must be disclosed. No compounding on disputed amounts",
     "effective_date": "2022-01-01", "applies_to": "credit_card"},
    {"id": "REG008", "source": "RBI", "title": "Dormant Account Guidelines",
     "description": "Accounts inactive 2 years classified dormant. No charges. KYC for reactivation",
     "effective_date": "2014-07-01", "applies_to": "dormant_accounts"},
]

# ── Save ─────────────────────────────────────────────────────────────────────
def save(data, filename):
    with open(DATA_DIR / filename, "w") as f:
        json.dump(data, f, indent=2, default=str)

save(customers, "mock_customers.json")
save(accounts, "mock_accounts.json")
save(transactions, "mock_transactions.json")
save(loans, "mock_loans.json")
save(products, "mock_products.json")
save(regulation_rules, "mock_regulation_rules.json")

print(f"Generated: {len(customers)} customers")
print(f"Generated: {len(accounts)} accounts")
print(f"Generated: {len(transactions)} transactions")
print(f"Generated: {len(loans)} loans")
print(f"Generated: {len(products)} products")
print(f"Generated: {len(regulation_rules)} regulation rules")