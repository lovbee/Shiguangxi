"""验证最终合规清洗会替换绝对化营销用词。"""

from app.services.compliance import ComplianceChecker


def test_absolute_claim_rewrite():
    checker = ComplianceChecker()
    assert "最好" not in checker.clean_text("这是最好的一款")
