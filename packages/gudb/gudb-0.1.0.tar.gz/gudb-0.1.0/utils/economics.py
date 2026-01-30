from typing import Dict, Union

# Constants for calculations
# Average AWS vCPU cost per hour (approximate blend of On-Demand types)
AWS_VCPU_HOURLY_RATE = 0.052  

# Manufacturing + Operational CO2 per hour of compute (approximate global average)
# Source: Cloud Carbon Footprint (kg CO2e / vCPUhr)
KG_CO2_PER_CPU_HOUR = 0.012 

def calculate_savings(
    original_duration_ms: float, 
    optimized_duration_ms: float, 
    daily_query_count: int = 10000
) -> Dict[str, Union[float, str]]:
    """
    Calculate financial and environmental savings based on query optimization.
    
    Args:
        original_duration_ms: Execution time before optimization
        optimized_duration_ms: Execution time after optimization
        daily_query_count: Number of times this query runs per day (default 10k)
        
    Returns:
        Dictionary with calculation results
    """
    if original_duration_ms <= optimized_duration_ms:
        return {
            "status": "no_savings",
            "monthly_usd": 0.0,
            "annual_co2_kg": 0.0,
            "cpu_hours_saved_monthly": 0.0
        }
    
    # Calculate time saved per day in milliseconds
    ms_saved_per_run = original_duration_ms - optimized_duration_ms
    ms_saved_daily = ms_saved_per_run * daily_query_count
    
    # Convert to hours
    # ms -> seconds -> minutes -> hours
    hours_saved_daily = ms_saved_daily / (1000 * 60 * 60)
    
    # Monthly savings (30 days)
    hours_saved_monthly = hours_saved_daily * 30
    
    # Financial Savings (USD)
    # We assume linear scaling: less CPU time = less compute cost
    # For serverless (Lambda/Fargate) this is direct. 
    # For EC2/RDS, this frees up capacity, delaying upgrades.
    monthly_usd = hours_saved_monthly * AWS_VCPU_HOURLY_RATE
    
    # Carbon Savings (kg CO2e)
    # Annualize it for impact
    annual_hours_saved = hours_saved_daily * 365
    annual_co2_kg = annual_hours_saved * KG_CO2_PER_CPU_HOUR
    
    return {
        "status": "success",
        "monthly_usd": round(monthly_usd, 2),
        "annual_co2_kg": round(annual_co2_kg, 2),
        "cpu_hours_saved_monthly": round(hours_saved_monthly, 2),
        "assumptions": {
            "daily_queries": daily_query_count,
            "cost_per_cpu_hr": AWS_VCPU_HOURLY_RATE,
            "co2_per_cpu_hr": KG_CO2_PER_CPU_HOUR
        }
    }
