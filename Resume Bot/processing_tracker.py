# Process Tracker : Tracks the number of processed resumes (saved + ignored) and updates the state manager accordingly.
class ProcessingTracker:

    def __init__(self, state_manager):
        self.state_manager = state_manager

    def saved(self):
        """Called when resume is successfully saved"""
        self.state_manager.increment_processed()

    def ignored(self):
        """Called when document processing ends in ignore"""
        self.state_manager.increment_processed()