def calculate_pm25_aqi(pm25: float) -> int:
    """Standard US EPA PM2.5 to AQI conversion"""
    if pm25 < 0: return 0
    if pm25 <= 12.0: return int((50/12.0) * pm25)
    if pm25 <= 35.4: return int(((100-51)/(35.4-12.1)) * (pm25-12.1) + 51)
    if pm25 <= 55.4: return int(((150-101)/(55.4-35.5)) * (pm25-35.5) + 101)
    if pm25 <= 150.4: return int(((200-151)/(150.4-55.5)) * (pm25-55.5) + 151)
    if pm25 <= 250.4: return int(((300-201)/(250.4-150.5)) * (pm25-150.5) + 201)
    return int(((500-301)/(500.4-250.5)) * (pm25-250.5) + 301)