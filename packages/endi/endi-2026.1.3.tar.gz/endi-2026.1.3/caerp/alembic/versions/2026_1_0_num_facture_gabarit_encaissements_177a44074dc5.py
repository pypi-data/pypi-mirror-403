"""
2026.1.0 Ajoute le numéro de facture au gabarit des écritures d'encaissement si besoin
"""
revision = "177a44074dc5"
down_revision = "747104e5974b"


def update_database_structure():
    pass


def migrate_datas():
    from zope.sqlalchemy import mark_changed

    from caerp.models.base import DBSESSION
    from caerp.models.config import Config

    session = DBSESSION()

    payment_template = Config.get_value("bookentry_payment_label_template")
    if "invoice.official_number" not in payment_template:
        Config.set(
            "bookentry_payment_label_template",
            f"{{invoice.official_number}} {payment_template}",
        )

    mark_changed(session)
    session.flush()


def upgrade():
    update_database_structure()
    migrate_datas()


def downgrade():
    pass
