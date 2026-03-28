from dotenv import load_dotenv
from flask import Blueprint, jsonify

from clockfy.clockfy_tags import ClockifyTags

load_dotenv()

clock_tags_route = Blueprint("CLOCK_TAGS", __name__)


@clock_tags_route.route("/clock/tags/update", methods=["PUT"])
def general_update():
    try:
        clock_tags = ClockifyTags()
        updates = clock_tags.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
