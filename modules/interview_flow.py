class InterviewFlow:
    def __init__(self, questions, conclusion_text):
        """
        questions: List of strings
            [greeting, profile, q1, q2, ..., q6]
        conclusion_text: str
        """
        self.questions = questions
        self.conclusion_text = conclusion_text
        self.index = 0  # Current question index
        self.advance_to_next_question = False
        self.confirmation_needed = False

    def current_question(self):
        if self.is_over():
            return None
        return self.questions[self.index]

    def is_over(self):
        # The interview is over after the last question (index 7) is asked.
        # Questions list has length 8 (greeting + profile + 6 questions)
        # So we check if the index has passed the last question.
        return self.index >= len(self.questions)

    def check_for_commands(self, transcript_lower: str, current_index: int):
        """
        Checks for special phrases to advance the interview state.
        """
        if current_index == 1 and "i am ready for questions" in transcript_lower:
            self.advance_to_next_question = True
        elif current_index > 1 and current_index < len(self.questions) - 1:
            if "i am ready for next question" in transcript_lower:
                self.confirmation_needed = True
            elif self.confirmation_needed and "yes please" in transcript_lower:
                self.advance_to_next_question = True
                self.confirmation_needed = False
