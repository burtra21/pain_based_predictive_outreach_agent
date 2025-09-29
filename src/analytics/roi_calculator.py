class ROICalculator:
    def __init__(self):
        self.metrics = {
            'avg_deal_size': 75000,
            'close_rate': 0.15,
            'sales_cycle_days': 45,
            'cost_per_lead': 50,
            'monthly_costs': 5000  # Tools + infrastructure
        }
    
    def calculate_monthly_roi(self, month: int = 1) -> Dict:
        """Calculate expected ROI by month"""
        # Ramp-up curve
        ramp_multipliers = {
            1: 0.3, 2: 0.5, 3: 0.7,
            4: 0.85, 5: 0.95, 6: 1.0
        }
        
        multiplier = ramp_multipliers.get(month, 1.0)
        
        # Expected outcomes
        leads_generated = 500 * multiplier
        qualified_leads = leads_generated * 0.3
        opportunities = qualified_leads * 0.4
        closed_deals = opportunities * self.metrics['close_rate']
        
        # Revenue
        revenue = closed_deals * self.metrics['avg_deal_size']
        
        # Costs
        lead_costs = leads_generated * self.metrics['cost_per_lead']
        total_costs = lead_costs + self.metrics['monthly_costs']
        
        # ROI
        roi = (revenue - total_costs) / total_costs * 100
        
        return {
            'month': month,
            'leads': int(leads_generated),
            'qualified': int(qualified_leads),
            'opportunities': int(opportunities),
            'closed_deals': closed_deals,
            'revenue': revenue,
            'costs': total_costs,
            'roi_percent': roi,
            'payback_months': total_costs / (revenue / month) if revenue > 0 else None
        }
    
    def project_annual(self) -> Dict:
        """Project annual performance"""
        annual = {
            'total_revenue': 0,
            'total_costs': 0,
            'total_deals': 0,
            'months': []
        }
        
        for month in range(1, 13):
            month_data = self.calculate_monthly_roi(month)
            annual['months'].append(month_data)
            annual['total_revenue'] += month_data['revenue']
            annual['total_costs'] += month_data['costs']
            annual['total_deals'] += month_data['closed_deals']
        
        annual['annual_roi'] = (
            (annual['total_revenue'] - annual['total_costs']) / 
            annual['total_costs'] * 100
        )
        
        return annual