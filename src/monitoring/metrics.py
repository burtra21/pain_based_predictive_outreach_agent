class MetricsTracker:
    def track_metrics(self):
        return {
            'data_collection': {
                'breaches_found': self.count_breaches_today(),
                'job_postings_found': self.count_jobs_today(),
                'companies_identified': self.count_new_companies()
            },
            'scoring': {
                'companies_scored': self.count_scored_today(),
                'avg_pain_score': self.average_pain_score(),
                'qualified_prospects': self.count_qualified()
            },
            'campaigns': {
                'campaigns_sent': self.count_sent_today(),
                'open_rate': self.calculate_open_rate(),
                'reply_rate': self.calculate_reply_rate(),
                'meeting_rate': self.calculate_meeting_rate()
            },
            'segments': {
                'post_breach': self.count_segment('post_breach_survivor'),
                'skills_gap': self.count_segment('skills_gap_sufferer'),
                'insurance': self.count_segment('insurance_pressured')
            }
        }