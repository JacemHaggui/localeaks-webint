# queries.py
from db import engine
from sqlalchemy import text

# =========================
# Apartment functions
# =========================
def fetch_apartments_by_address(address):
    """Return all apartments for a given address, including landlord, latest rent, charges, and average rating."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                a.id,
                a.number,
                a.floor,
                a.bedrooms,
                a.bathrooms,
                a.size_sqm,
                a.features,
                l.id AS landlord_id,
                l.name AS landlord_name,
                -- average overall rating
                ara.overall_average AS avg_overall,
                -- latest rent
                (SELECT rent_amount
                 FROM apartment_rent r
                 WHERE r.apartment_id = a.id
                 ORDER BY year DESC, month DESC
                 LIMIT 1) AS rent,
                -- latest charges
                (SELECT json_build_object(
                     'charges_amount', c.charges_amount,
                     'water', c.water,
                     'electricity', c.electricity,
                     'heating', c.heating,
                     'internet', c.internet,
                     'copropriete', c.copropriete,
                     'month', c.month,
                     'year', c.year
                 )
                 FROM apartment_charges c
                 WHERE c.apartment_id = a.id
                 ORDER BY year DESC, month DESC
                 LIMIT 1) AS charges
            FROM apartment a
            JOIN landlord l ON a.landlord_id = l.id
            LEFT JOIN apartment_review_average ara ON ara.apartment_id = a.id
            WHERE a.address = :address
            ORDER BY a.number
        """), {"address": address})

        apartments = []
        for row in result:
            apt = dict(row._mapping)
            # Nest landlord info
            apt["landlord"] = {"id": apt.pop("landlord_id"), "name": apt.pop("landlord_name")}
            # Average rating
            apt["average_reviews"] = {"overall": apt.pop("avg_overall")}
            apartments.append(apt)

        return apartments

def get_apartment_details(apartment_id):
    """Return apartment info, landlord info, averages, all reviews (with student names), latest rent, and latest charges."""
    with engine.connect() as conn:
        # Apartment info + landlord info + average grades
        result = conn.execute(text("""
            SELECT a.*, 
                   l.id AS landlord_id, l.name AS landlord_name,
                   ara.average_cleanliness, ara.average_amenities, ara.average_noise,
                   ara.average_safety, ara.average_value, ara.overall_average, ara.review_count AS avg_review_count
            FROM apartment a
            JOIN landlord l ON a.landlord_id = l.id
            LEFT JOIN apartment_review_average ara ON ara.apartment_id = a.id
            WHERE a.id = :apartment_id
        """), {"apartment_id": apartment_id})

        apartment = result.fetchone()
        if not apartment:
            return None

        apartment_data = dict(apartment._mapping)

        # Separate landlord info
        apartment_data["landlord"] = {
            "id": apartment_data.pop("landlord_id"),
            "name": apartment_data.pop("landlord_name")
        }

        # Average reviews
        apartment_data["average_reviews"] = {
            "cleanliness": apartment_data.pop("average_cleanliness"),
            "amenities": apartment_data.pop("average_amenities"),
            "noise": apartment_data.pop("average_noise"),
            "safety": apartment_data.pop("average_safety"),
            "value": apartment_data.pop("average_value"),
            "overall": apartment_data.pop("overall_average"),
            "review_count": apartment_data.pop("avg_review_count")
        }

        # All reviews for this apartment, including student names
        result = conn.execute(text("""
            SELECT r.*, s.name AS student_name
            FROM apartment_review r
            JOIN student s ON r.student_id = s.id
            WHERE r.apartment_id = :apartment_id
            ORDER BY r.created_at DESC
        """), {"apartment_id": apartment_id})

        apartment_data["reviews"] = [dict(row._mapping) for row in result]

        # Latest rent
        result = conn.execute(text("""
            SELECT rent_amount, month, year
            FROM apartment_rent
            WHERE apartment_id = :apartment_id
            ORDER BY year DESC, month DESC
            LIMIT 1
        """), {"apartment_id": apartment_id})
        rent_row = result.fetchone()
        apartment_data["rent"] = float(rent_row._mapping["rent_amount"]) if rent_row else None

        # Latest charges
        result = conn.execute(text("""
            SELECT charges_amount, water, electricity, heating, internet, copropriete, month, year
            FROM apartment_charges
            WHERE apartment_id = :apartment_id
            ORDER BY year DESC, month DESC
            LIMIT 1
        """), {"apartment_id": apartment_id})
        charges_row = result.fetchone()
        apartment_data["charges"] = dict(charges_row._mapping) if charges_row else None

        # --- Apartment photos ---
        result = conn.execute(text("""
            SELECT url
            FROM apartment_photo
            WHERE apartment_id = :apartment_id
        """), {"apartment_id": apartment_id})

        apartment_data["photos"] = [row._mapping["url"] for row in result]

        return apartment_data
# =========================
# Landlord functions
# =========================
def get_landlord_details(landlord_id):
    """Return landlord info, their apartments, averages, and all reviews (with student names)."""
    with engine.connect() as conn:
        # --- Landlord info + averages ---
        result = conn.execute(text("""
            SELECT l.*, 
                   lra.average_responsiveness, lra.average_maintenance,
                   lra.average_communication, lra.average_fairness, 
                   lra.overall_average, lra.review_count AS avg_review_count
            FROM landlord l
            LEFT JOIN landlord_review_average lra ON lra.landlord_id = l.id
            WHERE l.id = :landlord_id
        """), {"landlord_id": landlord_id})

        landlord = result.fetchone()
        if not landlord:
            return None

        landlord_data = dict(landlord._mapping)

        # --- Average ratings ---
        landlord_data["average_reviews"] = {
            "responsiveness": landlord_data.pop("average_responsiveness"),
            "maintenance": landlord_data.pop("average_maintenance"),
            "communication": landlord_data.pop("average_communication"),
            "fairness": landlord_data.pop("average_fairness"),
            "overall": landlord_data.pop("overall_average"),
            "review_count": landlord_data.pop("avg_review_count")
        }

        # --- Apartments for this landlord ---
        result = conn.execute(text("""
            SELECT id, number, floor, bedrooms, features, address
            FROM apartment
            WHERE landlord_id = :landlord_id
            ORDER BY number
        """), {"landlord_id": landlord_id})
        landlord_data["apartments"] = [dict(row._mapping) for row in result]

        # --- Reviews with student names ---
        result = conn.execute(text("""
            SELECT lr.*, s.name AS student_name
            FROM landlord_review lr
            JOIN student s ON lr.student_id = s.id
            WHERE lr.landlord_id = :landlord_id
            ORDER BY lr.created_at DESC
        """), {"landlord_id": landlord_id})

        landlord_data["reviews"] = []
        for row in result:
            review = dict(row._mapping)
            review["author"] = review.pop("student_name", None) or f"Étudiant {review['student_id']}"
            landlord_data["reviews"].append(review)

        return landlord_data
    

## ADDING STUFF -----------
from datetime import datetime


def add_apartment(apartment_data, reported_by=None):
    """
    Adds a new apartment with optional rent and charges.
    `reported_by` can be provided to set the reporter for rent/charges.
    """
    with engine.begin() as conn:
        # 1️⃣ Insert apartment
        result = conn.execute(
            text("""
                INSERT INTO apartment 
                    (landlord_id, number, floor, bedrooms, bathrooms, size_sqm, features, address)
                VALUES 
                    (:landlord_id, :number, :floor, :bedrooms, :bathrooms, :size_sqm, :features, :address)
                RETURNING id
            """),
            {
                'landlord_id': apartment_data['landlord_id'],
                'number': apartment_data.get('number'),
                'floor': apartment_data.get('floor'),
                'bedrooms': apartment_data['bedrooms'],
                'bathrooms': apartment_data['bathrooms'],
                'size_sqm': apartment_data.get('size_sqm'),
                'features': apartment_data.get('features'),
                'address': apartment_data['address']
            }
        )
        apartment_id = result.fetchone()[0]

        # 2️⃣ Insert rent if provided
        rent_data = apartment_data.get('apartment_rent', {})
        if rent_data:
            amount = rent_data.get('amount')
            month = rent_data.get('month')
            year = rent_data.get('year')
            if amount is not None and month is not None and year is not None:
                conn.execute(
                    text("""
                        INSERT INTO apartment_rent 
                            (apartment_id, rent_amount, month, year, reported_by, created_at)
                        VALUES 
                            (:apartment_id, :rent_amount, :month, :year, :reported_by, :created_at)
                    """),
                    {
                        'apartment_id': apartment_id,
                        'rent_amount': float(amount),
                        'month': int(month),
                        'year': int(year),
                        'reported_by': reported_by,
                        'created_at': datetime.now()
                    }
                )

        # 3️⃣ Insert charges if provided
        charges_data = apartment_data.get('apartment_charges', {})
        if charges_data:
            amount = charges_data.get('amount', 0)
            month = charges_data.get('month')
            year = charges_data.get('year')
            if month is not None and year is not None:
                conn.execute(
                    text("""
                        INSERT INTO apartment_charges 
                            (apartment_id, charges_amount, water, electricity, heating, internet, copropriete, month, year, reported_by, created_at)
                        VALUES 
                            (:apartment_id, :charges_amount, :water, :electricity, :heating, :internet, :copropriete, :month, :year, :reported_by, :created_at)
                    """),
                    {
                        'apartment_id': apartment_id,
                        'charges_amount': float(amount),
                        'water': bool(charges_data.get('water_included', False)),
                        'electricity': bool(charges_data.get('electricity_included', False)),
                        'heating': bool(charges_data.get('heating_included', False)),
                        'internet': bool(charges_data.get('internet_included', False)),
                        'copropriete': bool(charges_data.get('copropriete_included', False)),
                        'month': int(month),
                        'year': int(year),
                        'reported_by': reported_by,
                        'created_at': datetime.now()
                    }
                )

    return apartment_id
        
def add_landlord(landlord_data):
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO landlord (name, email, phone)
                VALUES (:name, :email, :phone)
                RETURNING id, name, email, phone
            """),
            landlord_data
        )
        return result.mappings().first()
        

# =========================
# SEARCH landlords by name
# =========================
def search_landlord_by_name(name: str, limit: int = 10):
    """
    Returns a list of landlords whose names contain the search string (case-insensitive).
    """
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                SELECT id, name
                FROM landlord
                WHERE LOWER(name) LIKE LOWER(:name)
                ORDER BY name
                LIMIT :limit
            """),
            {"name": f"%{name}%", "limit": limit}
        ).fetchall()
    return [{"id": row.id, "name": row.name} for row in result]
