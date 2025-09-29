class PerformanceOptimizer:
    def optimize_queries(self):
        """Optimize database queries"""
        # Add indexes
        queries = [
            "CREATE INDEX idx_domain ON company_universe(domain);",
            "CREATE INDEX idx_signal_date ON pain_signals(signal_date);",
            "CREATE INDEX idx_pain_score ON scored_prospects(pain_score);"
        ]
        
    def implement_caching(self):
        """Add Redis caching layer"""
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Cache company data for 1 hour
        def cache_company(domain: str, data: dict):
            r.setex(f"company:{domain}", 3600, json.dumps(data))
        
        # Cache scores for 24 hours
        def cache_score(domain: str, score: float):
            r.setex(f"score:{domain}", 86400, score)