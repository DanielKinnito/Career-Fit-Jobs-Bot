import pytest
from src.scraper.classifier import (
    classify_job_post,
    is_certified_job_post,
    extract_work_type,
)


def test_certified_job_post_standard():
    """Real structured job post from Ethiopian telegram channel must be accepted."""
    post = """
    Job Title: Senior Backend Developer
    Company: Tech Ethiopia PLC
    Location: Addis Ababa, Ethiopia (Remote Friendly)
    Job Type: Full-time

    Requirements:
    - BSc degree in Computer Science or Software Engineering
    - 3+ years of experience in Python, FastAPI, and PostgreSQL
    - Strong problem solving skills

    How to apply:
    Interested applicants can send their CV and portfolio to jobs@techethiopia.com
    Deadline: September 30, 2026
    """
    is_job, work_type, reasons = classify_job_post(post)
    assert is_job is True
    assert work_type == "Remote"
    assert is_certified_job_post(post) is True


def test_certified_job_post_amharic():
    """Real Amharic job vacancy post must be recognized."""
    post = """
    ክፍት የስራ ቦታ ማስታወቂያ
    የስራ መደብ፡ አካውንታንት (Accountant)
    ድርጅት፡ አዲስ ቢዝነስ ግሩፕ
    የትምህርት ደረጃ፡ በሂሳብ ወይም አግባብ ባለው ዲግሪ
    የስራ ልምድ፡ 2 ዓመት እና ከዚያ በላይ
    ደመወዝ፡ በስምምነት
    የማመልከቻ ጊዜ፡ እስከ መስከረም 15
    አመልካቾች ሲቪያችሁን በቴሌግራም @addis_hr ይላኩ።
    """
    is_job, work_type, reasons = classify_job_post(post)
    assert is_job is True
    assert is_certified_job_post(post) is True


def test_reject_charity_and_donation_appeal():
    """Donation, medical aid, or fundraiser post must be rejected."""
    post = """
    Please help our brother in need!
    We are raising funds for medical treatment and kidney transplant.
    Any donation counts. Please work together to help this family.
    Send your financial assistance to CBE account 100023456789.
    God bless you for your support.
    """
    is_job, work_type, reasons = classify_job_post(post)
    assert is_job is False
    assert is_certified_job_post(post) is False
    assert any("charity" in r.lower() or "donation" in r.lower() or "negative" in r.lower() for r in reasons)


def test_reject_cv_writing_service_promo():
    """Post offering CV writing or redesign services must be rejected."""
    post = """
    Do you need a professional CV that gets you hired?
    We provide professional CV writing services and resume revamp!
    Get an ATS-friendly resume for only 300 ETB.
    Contact our CV writing experts today @cv_services_ethio.
    """
    is_job, work_type, reasons = classify_job_post(post)
    assert is_job is False
    assert is_certified_job_post(post) is False


def test_reject_training_and_bootcamp_sales():
    """Course or bootcamp enrollment sales must be rejected."""
    post = """
    Digital Marketing Masterclass & Training Bootcamp!
    Learn SEO, Social Media Ads, and Content Creation in 6 weeks.
    Registration fee: 1,500 ETB. Limited seats available.
    Enroll now by contacting @training_admin. Class starts Monday!
    """
    is_job, work_type, reasons = classify_job_post(post)
    assert is_job is False
    assert is_certified_job_post(post) is False


def test_reject_job_seeker_ad():
    """A job seeker posting 'I am looking for a job' must be rejected."""
    post = """
    Hello everyone, I am a fresh graduate in Civil Engineering looking for a job.
    I have skills in AutoCAD and structural design.
    If any company is hiring or has an opening for junior engineer, please hire me.
    Contact me at @my_telegram_handle.
    """
    is_job, work_type, reasons = classify_job_post(post)
    assert is_job is False
    assert is_certified_job_post(post) is False


def test_reject_crypto_and_earning_scams():
    """Crypto airdrop, trading signals, or ponzi scheme must be rejected."""
    post = """
    Earn 5000 ETB daily from home with online task work!
    No experience needed. Free VIP trading signals and crypto investment.
    Join our channel to get daily airdrops and start earning today.
    """
    is_job, work_type, reasons = classify_job_post(post)
    assert is_job is False
    assert is_certified_job_post(post) is False


def test_reject_too_short_text():
    """Very short chatter or forward link must be rejected."""
    assert is_certified_job_post("Check this out: https://t.me/example") is False
    assert is_certified_job_post("Any open jobs today?") is False


def test_extract_work_type_modalities():
    """Work type extraction correctly identifies Remote, Hybrid, On-site."""
    assert extract_work_type("This is a 100% remote job for Python devs.") == "Remote"
    assert extract_work_type("Work from home opportunity for translators.") == "Remote"
    assert extract_work_type("Hybrid position: 2 days office, 3 days home.") == "Hybrid"
    assert extract_work_type("On-site role located at Bole Medhanialem, Addis Ababa.") == "On-site"
    assert extract_work_type("General position in Addis Ababa.") == "On-site"
    assert extract_work_type("Random text without clear place.") == "Unspecified"
