-- =========================
-- Function to update apartment averages incrementally on delete
-- =========================
CREATE OR REPLACE FUNCTION update_apartment_review_average_on_delete()
RETURNS TRIGGER AS $$
DECLARE
    new_count INT;
BEGIN
    SELECT review_count - 1 INTO new_count
    FROM apartment_review_average
    WHERE apartment_id = OLD.apartment_id;

    IF new_count > 0 THEN
        UPDATE apartment_review_average
        SET
            average_cleanliness = (average_cleanliness * review_count - OLD.cleanliness) / new_count,
            average_amenities   = (average_amenities   * review_count - OLD.amenities)   / new_count,
            average_noise       = (average_noise       * review_count - OLD.noise)       / new_count,
            average_safety      = (average_safety      * review_count - OLD.safety)      / new_count,
            average_value       = (average_value       * review_count - OLD.value_for_money) / new_count,
            overall_average     = (overall_average     * review_count - OLD.overall) / new_count,
            review_count        = new_count
        WHERE apartment_id = OLD.apartment_id;
    ELSE
        -- No more reviews, reset averages
        UPDATE apartment_review_average
        SET
            average_cleanliness = NULL,
            average_amenities = NULL,
            average_noise = NULL,
            average_safety = NULL,
            average_value = NULL,
            overall_average = NULL,
            review_count = 0
        WHERE apartment_id = OLD.apartment_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =========================
-- Trigger to call function after a review is deleted
-- =========================
CREATE TRIGGER apartment_review_delete_trigger
AFTER DELETE ON apartment_review
FOR EACH ROW
EXECUTE FUNCTION update_apartment_review_average_on_delete();


-- =========================
-- Function to update landlord averages incrementally on delete
-- =========================
CREATE OR REPLACE FUNCTION update_landlord_review_average_on_delete()
RETURNS TRIGGER AS $$
DECLARE
    new_count INT;
BEGIN
    SELECT review_count - 1 INTO new_count
    FROM landlord_review_average
    WHERE landlord_id = OLD.landlord_id;

    IF new_count > 0 THEN
        UPDATE landlord_review_average
        SET
            average_responsiveness = (average_responsiveness * review_count - OLD.responsiveness) / new_count,
            average_maintenance    = (average_maintenance    * review_count - OLD.maintenance)    / new_count,
            average_communication  = (average_communication  * review_count - OLD.communication)  / new_count,
            average_fairness       = (average_fairness       * review_count - OLD.fairness)       / new_count,
            overall_average        = (overall_average        * review_count - OLD.overall)        / new_count,
            review_count           = new_count
        WHERE landlord_id = OLD.landlord_id;
    ELSE
        -- No more reviews, reset averages
        UPDATE landlord_review_average
        SET
            average_responsiveness = NULL,
            average_maintenance = NULL,
            average_communication = NULL,
            average_fairness = NULL,
            overall_average = NULL,
            review_count = 0
        WHERE landlord_id = OLD.landlord_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =========================
-- Trigger to call function after a landlord review is deleted
-- =========================
CREATE TRIGGER landlord_review_delete_trigger
AFTER DELETE ON landlord_review
FOR EACH ROW
EXECUTE FUNCTION update_landlord_review_average_on_delete();