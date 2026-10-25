from pydantic import BaseModel, Field
from typing import Literal


class InsightSchemaV2(BaseModel):
    """
    PM-grade classification schema for Myntra wishlist conversion discovery.
    Answers: WHY users don't convert, not just WHAT they complained about.
    """

    # ── Core intent (Q1, Q8) ─────────────────────────────────────────────────
    intent: Literal[
        'Purchase-Ready',    # User clearly intends to buy soon
        'Deferred-Intent',   # Genuine purchase intent but something is blocking
        'Browse-Saving',     # Wishlist used as bookmarking, no real purchase plan
        'Complaint',         # Post-purchase or app experience complaint
        'Comparison',        # Actively shortlisting / comparing products
        'Unknown'
    ] = Field(description="Primary intent. Distinguish between genuine deferred purchase vs casual browse-saving.")

    # ── Friction (Q2, Q3) ────────────────────────────────────────────────────
    friction_category: Literal[
        'Fit/Size',           # Uncertainty about fit, sizing, measurements
        'Fabric/Material',    # Texture, quality, durability concerns
        'Trust/Authenticity', # Brand trust, seller authenticity, review credibility
        'Styling/Occasion',   # Unsure how to style it or if it fits their occasion
        'Social-Validation',  # Needs peer/influencer approval before buying
        'Delivery/Return',    # Delivery time, return policy friction
        'UX/App',             # App or website experience issues
        'None'
    ] = Field(description="The primary conversion blocker. Styling/Occasion = unsure how to wear/when to wear. Social-Validation = needs someone else's approval.")

    severity: Literal['Low', 'Medium', 'High'] = Field(
        description="High = actively blocked purchase or caused return. Medium = hesitating. Low = minor annoyance."
    )

    # ── Wishlist behavior (Q1, Q8) ───────────────────────────────────────────
    wishlist_mode: Literal[
        'Genuine-Intent',    # Will buy, just waiting (salary, occasion, sale)
        'Browse-Saving',     # Liked it but no real plan to buy
        'Price-Waiting',     # Waiting for discount or sale
        'Occasion-Waiting',  # Buying for a specific future event
        'Unclear'
    ] = Field(description="Is the wishlist being used as a deferred purchase tool or just a save/bookmark? Look for signals like 'will buy after salary', 'just liked it', 'waiting for sale'.")

    # ── Postponement trigger (Q2, Q4) ────────────────────────────────────────
    postponement_trigger: Literal[
        'Size-Doubt',           # Cannot decide size, no confidence in fit
        'Price-Wait',           # Waiting for discount, sale, or paycheck
        'Occasion-Not-Yet',     # Buying for future wedding, trip, festival etc.
        'Wants-More-Reviews',   # Needs more social proof before committing
        'Comparing-Options',    # Still shortlisting, hasn't decided yet
        'None'                  # No postponement — immediate action or complaint
    ] = Field(description="The single most important reason purchase is being delayed.")

    # ── Comparison behavior (Q5) ─────────────────────────────────────────────
    comparison_dimension: Literal[
        'Price',           # Comparing prices across platforms/sellers
        'Brand',           # Comparing brand reputation or alternatives
        'Fit',             # Comparing sizing between similar products
        'Reviews',         # Comparing review quality/quantity
        'Style',           # Comparing visual appeal / styling options
        'Not-Comparing'    # Not in a comparison mode
    ] = Field(description="If the user is comparing, what dimension are they comparing on?")

    # ── External information seeking (Q6) ────────────────────────────────────
    external_source: Literal[
        'YouTube',      # Watching haul/review videos
        'Instagram',    # Checking influencer posts/reels
        'Reddit',       # Asking community opinions
        'Friend',       # Asking friends/family
        'Brand-Site',   # Going to brand's own website
        'None'          # No external seeking mentioned
    ] = Field(description="Where is the user going outside Myntra for information or validation?")

    # ── Decision factors (Q7) ────────────────────────────────────────────────
    decision_factors: str = Field(
        description="Comma-separated list of factors mentioned. Choose from: Fit, Size, Price, Reviews, Occasion, Styling, Social-Proof, Brand, Fabric. Example: 'Fit,Size,Reviews'"
    )

    # ── Unmet need (Q10, Q11) ────────────────────────────────────────────────
    unmet_need: str = Field(
        description="Complete this sentence: 'User would buy if Myntra provided ___' or 'User cannot buy because Myntra lacks ___'. Be specific and actionable for a PM."
    )

    # ── Segment signal (Q9) ──────────────────────────────────────────────────
    user_segment_signal: Literal[
        'Student',               # Budget-conscious, trend-aware
        'Working-Professional',  # Willing to spend, time-poor
        'Occasion-Shopper',      # Buying for events: weddings, festivals
        'Deal-Hunter',           # Primarily motivated by discounts
        'Trend-Follower',        # Driven by what's popular/influencer-driven
        'Unclear'
    ] = Field(description="Infer user segment from language, price sensitivity, and context clues.")

    # ── Summary ──────────────────────────────────────────────────────────────
    summary: str = Field(
        description="One sentence: what is the user's core problem and what would make them convert?"
    )


# Keep original schema name as alias for backward compatibility
InsightSchema = InsightSchemaV2
