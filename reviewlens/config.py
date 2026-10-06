APP_TITLE = "ReviewLens AI"
APP_SUBTITLE = "Regional customer intelligence / 2026"

CATEGORIES = ["Delivery", "Price", "Product Quality", "Support", "UX"]

COLUMN_ALIASES = {
    "review_text": [
        "review_text", "review text", "reviewtext",
        "customer_review", "customer review", "customerreview",
        "review_content", "review content", "reviewcontent",
        "review_body", "review body", "reviewbody",
        "customer_feedback", "customer feedback", "customerfeedback",
        "user_feedback", "user feedback", "userfeedback",
        "customer_comment", "customer comment", "customercomment",
        "review", "reviews",
        "comment", "comments",
        "feedback",
        "opinion", "opinions",
        "remarks", "remark",
        "response", "responses",
        "message", "messages",
        "description",
        "text",
        "body",
    ],
    "region": [
        "region", "city", "location", "area", "zone", "market",
        "state", "place", "territory",
    ],
    "category": [
        "category", "complaint_category", "complaint category", "topic",
        "issue", "type", "complaint", "complaints",
    ],
    "rating": [
        "rating", "stars", "score", "review_rating", "review rating",
        "ratings", "star_rating", "star rating",
    ],
    "date": [
        "date", "review_date", "review date", "created_at", "created at",
        "timestamp", "datetime", "date_time", "published_at", "published at",
    ],
    "review_id": [
        "review_id", "review id", "id", "reviewid", "uuid", "uid",
    ],
}

NEGATIVE_WORDS = [
    "late", "bad", "poor", "terrible", "slow", "problem", "issue",
    "disappoint", "frustrat", "expensive", "confusing", "failed",
    "worst", "broken", "delay", "refund", "damaged", "unhelpful",
]

POSITIVE_WORDS = [
    "good", "great", "excellent", "happy", "fast", "smooth", "easy",
    "love", "best", "quick", "helpful", "perfect", "amazing",
]
