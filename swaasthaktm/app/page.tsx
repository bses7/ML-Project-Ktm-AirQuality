"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Wind,
  Droplets,
  Eye,
  Gauge,
  Heart,
  ShieldAlert,
  TrendingUp,
  Clock,
} from "lucide-react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface DashboardData {
  aqi: number;
  pm25: number;
  pm10: number;
  humidity: number;
  visibility: number;
  timestamp: string;
  hazard_level: string;
  health_recommendations: string[];
}

interface HistoricalData {
  timestamp: string;
  pm25: number;
  temp: number;
  humidity: number;
  windspeed: number;
  aqi: number;
}

interface AQIDistribution {
  hour: string;
  count: number;
  category: string;
  aqi: number;
}

const getAQIColor = (aqi: number) => {
  if (aqi <= 50)
    return {
      bg: "bg-[#00E400]",
      text: "text-[#00E400]",
      color: "#00E400",
      badgeText: "text-white",
      label: "Good",
      desc: "Air quality is satisfactory",
    };
  if (aqi <= 100)
    return {
      bg: "bg-[#FDFD96]",
      text: "text-[#000000]",
      color: "#FDFD96",
      badgeText: "text-gray-900",
      label: "Moderate",
      desc: "Acceptable air quality",
    };
  if (aqi <= 150)
    return {
      bg: "bg-[#FF7E00]",
      text: "text-[#FF7E00]",
      color: "#FF7E00",
      badgeText: "text-white",
      label: "Unhealthy for Sensitive Groups",
      desc: "Members of sensitive groups may experience health effects",
    };
  if (aqi <= 200)
    return {
      bg: "bg-[#FF0000]",
      text: "text-[#FF0000]",
      color: "#FF0000",
      badgeText: "text-white",
      label: "Unhealthy",
      desc: "Some members of the general public may experience health effects",
    };
  if (aqi <= 300)
    return {
      bg: "bg-[#8F3F97]",
      text: "text-[#8F3F97]",
      color: "#8F3F97",
      badgeText: "text-white",
      label: "Very Unhealthy",
      desc: "Health alert: the entire population is more likely to be affected",
    };
  return {
    bg: "bg-[#7E0023]",
    text: "text-[#7E0023]",
    color: "#7E0023",
    badgeText: "text-white",
    label: "Hazardous",
    desc: "Health warning of emergency conditions",
  };
};

const AQIGauge = ({ aqi }: { aqi: number }) => {
  const percentage = Math.min((aqi / 500) * 100, 100);
  const aqiColor = getAQIColor(aqi);
  return (
    <div className="relative w-32 h-32 mx-auto">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="#E0E0E0"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={aqiColor.color}
          strokeWidth="8"
          strokeDasharray={`${(percentage / 100) * 282.7} 282.7`}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-bold ${aqiColor.text}`}>{aqi}</span>
        <span className="text-xs text-gray-500">AQI</span>
      </div>
    </div>
  );
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-xs text-gray-500 mb-1">
          {new Date(payload[0].payload.timestamp).toLocaleString()}
        </p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}:{" "}
            <span className="font-bold">{entry.value.toFixed(1)}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [historical, setHistorical] = useState<HistoricalData[]>([]);
  const [aqiDistribution, setAqiDistribution] = useState<AQIDistribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/dashboard");
        if (!response.ok) throw new Error("Failed to fetch dashboard data");
        const json = await response.json();
        setData(json);
        setError(null);

        try {
          const historicalRes = await fetch(
            "http://localhost:8000/api/historical",
          );
          if (historicalRes.ok) {
            const hist = await historicalRes.json();
            setHistorical(hist);
          }
        } catch (e) {
          console.log("Historical data not available");
        }

        try {
          const distributionRes = await fetch(
            "http://localhost:8000/api/aqi-distribution",
          );
          if (distributionRes.ok) {
            const dist = await distributionRes.json();
            setAqiDistribution(dist);
          }
        } catch (e) {
          console.log("AQI distribution data not available");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-50 p-4 md:p-8">
        <div className="max-w-7xl mx-auto flex items-center justify-center h-screen">
          <div className="text-center">
            <Gauge className="w-12 h-12 mx-auto mb-4 animate-spin text-indigo-600" />
            <p className="text-gray-600">Loading air quality data...</p>
          </div>
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-50 p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white border border-red-200 rounded-lg shadow-md p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-6 h-6 text-red-600 mt-1 shrink-0" />
              <div>
                <h3 className="font-semibold text-red-900 mb-1">
                  Connection Error
                </h3>
                <p className="text-sm text-gray-600">
                  {error || "Unable to load dashboard data"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  const aqiColor = getAQIColor(data.aqi);

  return (
    <main className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Swaastha-Ktm
          </h1>
          <p className="text-gray-600">
            Medical Air Quality Dashboard for Kathmandu
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Last updated: {new Date(data.timestamp).toLocaleDateString()}{" "}
            {new Date(data.timestamp).toLocaleTimeString()}
          </p>
        </header>

        <div className="grid grid-cols-12 gap-4">
          {/* Main AQI Card - Large, spans 2 rows */}
          <div className="bg-white rounded-lg p-6 shadow-lg col-span-12 md:col-span-5 md:row-span-2">
            <div className="h-full flex flex-col justify-center">
              <AQIGauge aqi={data.aqi} />
              <div className="mt-6 text-center">
                <h2 className="text-2xl font-bold mb-2">{aqiColor.label}</h2>
                <p className="text-gray-600 mb-4 text-sm">{aqiColor.desc}</p>
                <div
                  className={`inline-block px-4 py-2 rounded-lg ${aqiColor.bg} ${aqiColor.badgeText} font-semibold`}
                >
                  AQI: {data.aqi}
                </div>
              </div>
            </div>
          </div>

          {/* PM2.5 Card */}
          <div className="bg-white rounded-lg p-4 shadow-md col-span-6 md:col-span-3">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-gray-600 text-xs mb-1">PM 2.5</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.pm25.toFixed(1)}
                </p>
                <p className="text-xs text-gray-500 mt-1">μg/m³</p>
              </div>
              <Wind className="w-8 h-8 text-indigo-400 opacity-50" />
            </div>
          </div>

          {/* PM10 Card */}
          <div className="bg-white rounded-lg p-4 shadow-md col-span-6 md:col-span-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-gray-600 text-xs mb-1">PM 10</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.pm10.toFixed(1)}
                </p>
                <p className="text-xs text-gray-500 mt-1">μg/m³</p>
              </div>
              <Wind className="w-8 h-8 text-indigo-400 opacity-50" />
            </div>
          </div>

          {/* Humidity Card */}
          <div className="bg-white rounded-lg p-4 shadow-md col-span-6 md:col-span-4">
            <div className="h-full flex flex-col justify-between">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-gray-600 text-xs mb-1">Humidity</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {data.humidity.toFixed(0)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">%</p>
                </div>
                <Droplets className="w-8 h-8 text-blue-400 opacity-50" />
              </div>
            </div>
          </div>

          {/* Visibility Card */}
          <div className="bg-white rounded-lg p-4 shadow-md col-span-6 md:col-span-3">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-gray-600 text-xs mb-1">Visibility</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.visibility.toFixed(1)}
                </p>
                <p className="text-xs text-gray-500 mt-1">km</p>
              </div>
              <Eye className="w-8 h-8 text-purple-400 opacity-50" />
            </div>
          </div>

          {/* PM2.5 Trend Chart */}
          {historical.length > 0 && (
            <div className="bg-white rounded-lg p-4 shadow-lg col-span-12 md:col-span-7">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                <h3 className="text-lg font-bold text-gray-900">
                  PM2.5 Trend (24h)
                </h3>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={historical}>
                  <defs>
                    <linearGradient id="colorPM25" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8} />
                      <stop
                        offset="95%"
                        stopColor="#6366f1"
                        stopOpacity={0.1}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    }
                    stroke="#6b7280"
                    style={{ fontSize: "11px" }}
                  />
                  <YAxis stroke="#6b7280" style={{ fontSize: "11px" }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="pm25"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorPM25)"
                    name="PM2.5 (µg/m³)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Health Recommendations */}
          <div className="bg-white rounded-lg shadow-lg p-4 col-span-12 md:col-span-5">
            <div className="flex items-center gap-2 mb-3">
              <Heart className="w-5 h-5 text-red-500" />
              <h3 className="text-lg font-bold text-gray-900">
                Health Prescriptions
              </h3>
            </div>

            {/* Hazard Warning */}
            {data.hazard_level !== "Low" ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                <div className="flex items-start gap-2">
                  <ShieldAlert className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-red-900 text-sm mb-1">
                      Hazard Level: {data.hazard_level}
                    </h4>
                    <p className="text-xs text-red-800">
                      Air quality is not ideal. Consider taking precautions.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                <div className="flex items-start gap-2">
                  <Heart className="w-5 h-5 text-green-600 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-green-900 text-sm mb-1">
                      Air Quality Good
                    </h4>
                    <p className="text-xs text-green-800">
                      Current conditions are favorable for outdoor activities.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2 max-h-32.5 overflow-y-auto">
              {data.health_recommendations &&
              data.health_recommendations.length > 0 ? (
                data.health_recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 p-2 bg-blue-50 rounded-lg border border-blue-100"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                    <p className="text-xs text-gray-700">{rec}</p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-gray-500 italic">
                  No specific recommendations at this time.
                </p>
              )}
            </div>
            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-[10px] text-gray-600">
                <span className="font-semibold">Disclaimer:</span> These
                recommendations are generated using a trained machine learning
                model for informational purposes only. Final decisions should
                always be made by a qualified human professional and not solely
                based on this prediction.
              </p>
            </div>
          </div>

          {/* Environmental Metrics */}
          {historical.length > 0 && (
            <div className="bg-white rounded-lg p-4 shadow-lg col-span-12">
              <h3 className="text-lg font-bold text-gray-900 mb-3">
                Environmental Metrics
              </h3>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={historical}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    }
                    stroke="#6b7280"
                    style={{ fontSize: "11px" }}
                  />
                  <YAxis
                    yAxisId="left"
                    stroke="#6b7280"
                    style={{ fontSize: "11px" }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    stroke="#6b7280"
                    style={{ fontSize: "11px" }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: "12px" }} />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="pm25"
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={false}
                    name="PM2.5 (µg/m³)"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="temp"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={false}
                    name="Temperature (°C)"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="humidity"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="Humidity (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* AQI Distribution by Hour */}
          {aqiDistribution.length > 0 && (
            <div className="bg-white rounded-lg p-4 shadow-lg col-span-12">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-5 h-5 text-indigo-600" />
                <h3 className="text-lg font-bold text-gray-900">
                  AQI Patterns by Hour of Day
                </h3>
              </div>
              <p className="text-xs text-gray-600 mb-3">
                Average AQI levels throughout the day based on historical data
              </p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={aqiDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="hour"
                    stroke="#6b7280"
                    style={{ fontSize: "11px" }}
                  />
                  <YAxis stroke="#6b7280" style={{ fontSize: "11px" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Bar
                    dataKey="aqi"
                    fill="#6366f1"
                    radius={[8, 8, 0, 0]}
                    name="Average AQI"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <footer className="mt-8 text-center text-xs text-gray-500 space-y-1">
          <p>© {new Date().getFullYear()} Swaastha-Ktm. All rights reserved.</p>
          <p>Swaastha-Ktm Medical Air Quality Dashboard</p>
          <p>Providing real-time air quality insights for Kathmandu</p>
        </footer>
      </div>
    </main>
  );
}
