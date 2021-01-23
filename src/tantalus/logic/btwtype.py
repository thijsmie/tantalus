from tantalus_db.base import db
from tantalus_db.models import BtwType


def get_btwtype(percentage):
    percentage = int(percentage)
    btwtype = BtwType.query.filter(BtwType.percentage == percentage).first()

    if not btwtype:
        btwtype = BtwType(
            name=f"{percentage:02}%",
            percentage=percentage
        )
        db.session.add(btwtype)
    
    return btwtype