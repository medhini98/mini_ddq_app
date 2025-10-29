# mini_ddq_app/data_db.py
from datetime import date
from sqlalchemy import text as sa_text

from mini_ddq_app.db import SessionLocal
from mini_ddq_app.models.tenant import Tenant
from mini_ddq_app.models.user import User
from mini_ddq_app.models.questionnaire import Questionnaire
from mini_ddq_app.models.question import Question
from mini_ddq_app.auth.hashing import hash_password


def seed():
    db = SessionLocal()
    try:
        # Clear existing data in FK-safe order (responses -> questions -> questionnaires -> users -> tenants)
        db.execute(sa_text("TRUNCATE TABLE responses, questions, questionnaires, users, tenants RESTART IDENTITY CASCADE;"))
        db.commit()

        # ---- Tenants ----
        alpha = Tenant(org_name="AlphaCorp", contract_start=date.today())
        beta = Tenant(org_name="BetaInc", contract_start=date.today())
        db.add_all([alpha, beta])
        db.flush()  # to get alpha.id, beta.id

        # ---- Users (per tenant) ----
        alpha_admin = User(
            tenant_id=alpha.id,
            email="alice@alpha.com",
            first_name="Alice",
            last_name="Admin",
            password_hash=hash_password("alpha_admin"),
            role="admin",
        )
        alpha_analyst = User(
            tenant_id=alpha.id,
            email="alan@alpha.com",
            first_name="Alan",
            last_name="Analyst",
            password_hash=hash_password("alpha_analyst"),
            role="analyst",
        )
        alpha_viewer = User(
            tenant_id=alpha.id,
            email="ava@alpha.com",
            first_name="Ava",
            last_name="Viewer",
            password_hash=hash_password("alpha_viewer"),
            role="viewer",
        )

        beta_admin = User(
            tenant_id=beta.id,
            email="bob@beta.com",
            first_name="Bob",
            last_name="Admin",
            password_hash=hash_password("beta_admin"),
            role="admin",
        )
        beta_analyst = User(
            tenant_id=beta.id,
            email="bella@beta.com",
            first_name="Bella",
            last_name="Analyst",
            password_hash=hash_password("beta_analyst"),
            role="analyst",
        )
        beta_viewer = User(
            tenant_id=beta.id,
            email="ben@beta.com",
            first_name="Ben",
            last_name="Viewer",
            password_hash=hash_password("beta_viewer"),
            role="viewer",
        )

        db.add_all([alpha_admin, alpha_analyst, alpha_viewer, beta_admin, beta_analyst, beta_viewer])
        db.flush()  # to get user ids

        # ---- Questionnaires (must have created_by) ----
        alpha_ddq = Questionnaire(
            tenant_id=alpha.id,
            name="Default DDQ",
            created_by=alpha_admin.id,  # required by your model
            # status defaults to 'draft', version defaults to 1
        )
        beta_ddq = Questionnaire(
            tenant_id=beta.id,
            name="Default DDQ",
            created_by=beta_admin.id,
        )
        db.add_all([alpha_ddq, beta_ddq])
        db.flush()  # to get questionnaire ids

        # ---- Questions (require questionnaire_id; question_text maps to "text" column) ----
        alpha_q1 = Question(
            tenant_id=alpha.id,
            questionnaire_id=alpha_ddq.id,
            question_text="Does your org have a data backup policy?",
            display_order=1,
            is_required=False,
        )
        alpha_q2 = Question(
            tenant_id=alpha.id,
            questionnaire_id=alpha_ddq.id,
            question_text="Do you encrypt sensitive data?",
            display_order=2,
            is_required=True,
        )
        beta_q1 = Question(
            tenant_id=beta.id,
            questionnaire_id=beta_ddq.id,
            question_text="Does your org have a data backup policy?",
            display_order=1,
            is_required=False,
        )
        beta_q2 = Question(
            tenant_id=beta.id,
            questionnaire_id=beta_ddq.id,
            question_text="Do you encrypt sensitive data?",
            display_order=2,
            is_required=True,
        )

        db.add_all([alpha_q1, alpha_q2, beta_q1, beta_q2])
        db.commit()
        print("✅ Seed data inserted successfully!")

    except Exception as e:
        db.rollback()
        print("❌ Error seeding data:", e)
    finally:
        db.close()


if __name__ == "__main__":
    seed()