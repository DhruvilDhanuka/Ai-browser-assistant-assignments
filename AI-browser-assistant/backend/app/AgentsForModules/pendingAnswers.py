import threading

_pending_answers: dict[int, dict] = {}


def register_question(task_id: int) -> threading.Event:
    event = threading.Event()
    _pending_answers[task_id] = {"event": event, "answer": None}
    return event


def submit_answer(task_id: int, answer: str) -> bool:

    entry = _pending_answers[task_id]
    if entry is None:
        return False
    entry["answer"] = answer
    entry["event"].set()
    return True


def get_answer(task_id: int) -> str | None:
    entry = _pending_answers.pop(task_id, None)
    return entry["answer"] if entry else None
