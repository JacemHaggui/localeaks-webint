-- =========================
-- Function to update apartment averages incrementally
-- =========================
CREATE OR REPLACE FUNCTION update_apartment_review_average_incremental()
RETURNS TRIGGER AS $$
BEGIN
    -- If an average row already exists
    IF EXISTS (SELECT 1 FROM apartment_review_average WHERE apartment_id = NEW.apartment_id) THEN
        UPDATE apartment_review_average
        SET
            average_cleanliness = (average_cleanliness * review_count + NEW.cleanliness) / (review_count + 1),
            average_amenities   = (average_amenities   * review_count + NEW.amenities)   / (review_count + 1),
            average_noise       = (average_noise       * review_count + NEW.noise)       / (review_count + 1),
            average_safety      = (average_safety      * review_count + NEW.safety)      / (review_count + 1),
            average_value       = (average_value       * review_count + NEW.value_for_money) / (review_count + 1),
            overall_average     = (overall_average     * review_count + NEW.overall) / (review_count + 1),
            review_count        = review_count + 1
        WHERE apartment_id = NEW.apartment_id;
    ELSE
        -- First review for this apartment
        INSERT INTO apartment_review_average(
            apartment_id, average_cleanliness, average_amenities, average_noise,
            average_safety, average_value, overall_average, review_count
        )
        VALUES (
            NEW.apartment_id,
            NEW.cleanliness, NEW.amenities, NEW.noise,
            NEW.safety, NEW.value_for_money, NEW.overall,
            1
        );
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =========================
-- Trigger to call the function after a new apartment review is inserted
-- =========================
CREATE TRIGGER apartment_review_incremental_trigger
AFTER INSERT ON apartment_review
FOR EACH ROW
EXECUTE FUNCTION update_apartment_review_average_incremental();







-- =========================
-- Function to update landlord averages incrementally
-- =========================
CREATE OR REPLACE FUNCTION update_landlord_review_average_incremental()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM landlord_review_average WHERE landlord_id = NEW.landlord_id) THEN
        UPDATE landlord_review_average
        SET
            average_responsiveness = (average_responsiveness * review_count + NEW.responsiveness) / (review_count + 1),
            average_maintenance    = (average_maintenance    * review_count + NEW.maintenance)    / (review_count + 1),
            average_communication  = (average_communication  * review_count + NEW.communication)  / (review_count + 1),
            average_fairness       = (average_fairness       * review_count + NEW.fairness)       / (review_count + 1),
            overall_average        = (overall_average        * review_count + NEW.overall)        / (review_count + 1),
            review_count           = review_count + 1
        WHERE landlord_id = NEW.landlord_id;
    ELSE
        -- First review for this landlord
        INSERT INTO landlord_review_average(
            landlord_id, average_responsiveness, average_maintenance,
            average_communication, average_fairness, overall_average, review_count
        )
        VALUES (
            NEW.landlord_id, NEW.responsiveness, NEW.maintenance,
            NEW.communication, NEW.fairness, NEW.overall, 1
        );
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =========================
-- Trigger to call the function after a new landlord review is inserted
-- =========================
CREATE TRIGGER landlord_review_incremental_trigger
AFTER INSERT ON landlord_review
FOR EACH ROW
EXECUTE FUNCTION update_landlord_review_average_incremental();