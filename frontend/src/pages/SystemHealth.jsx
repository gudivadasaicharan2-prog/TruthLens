import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Server, Cpu, HardDrive, Clock, Activity, Zap, Shield, Database, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

/**
 * System Health Dashboard
 * 
 * Displays system metrics and health status for admin monitoring
 */
const SystemHealth = () => {
  const [healthData, setHealthData] = useState({
    backendStatus: 'operational',
    apiHealth: 'healthy',
    gpuStatus: 'available',
    cpuUsage: 45,
    memoryUsage: 62,
    modelVersion: 'v2.1.0',
    uptime: '15d 4h 32m',
    queueLength: 3,
    analysesCompleted: 15423,
    avgResponseTime: 1.2,
    accuracy: 94.7
  });

  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setHealthData(prev => ({
        ...prev,
        cpuUsage: Math.max(20, Math.min(95, prev.cpuUsage + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.max(40, Math.min(90, prev.memoryUsage + (Math.random() - 0.5) * 5)),
        queueLength: Math.max(0, prev.queueLength + Math.floor(Math.random() * 3) - 1),
        analysesCompleted: prev.analysesCompleted + Math.floor(Math.random() * 2),
      }));
      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'operational':
      case 'healthy':
      case 'available':
        return <CheckCircle className="w-5 h-5 text-success" />;
      case 'degraded':
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-warning" />;
      case 'down':
      case 'unavailable':
        return <XCircle className="w-5 h-5 text-danger" />;
      default:
        return <Activity className="w-5 h-5 text-accent" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational':
      case 'healthy':
      case 'available':
        return 'text-success';
      case 'degraded':
      case 'warning':
        return 'text-warning';
      case 'down':
      case 'unavailable':
        return 'text-danger';
      default:
        return 'text-accent';
    }
  };

  const getUsageColor = (value) => {
    if (value < 50) return 'text-success';
    if (value < 75) return 'text-warning';
    return 'text-danger';
  };

  const metrics = [
    {
      title: 'Backend Status',
      value: healthData.backendStatus,
      icon: Server,
      status: healthData.backendStatus,
      format: 'status'
    },
    {
      title: 'API Health',
      value: healthData.apiHealth,
      icon: Shield,
      status: healthData.apiHealth,
      format: 'status'
    },
    {
      title: 'GPU Status',
      value: healthData.gpuStatus,
      icon: Zap,
      status: healthData.gpuStatus,
      format: 'status'
    },
    {
      title: 'CPU Usage',
      value: `${healthData.cpuUsage.toFixed(1)}%`,
      icon: Cpu,
      status: healthData.cpuUsage < 75 ? 'healthy' : 'warning',
      format: 'percentage',
      rawValue: healthData.cpuUsage
    },
    {
      title: 'Memory Usage',
      value: `${healthData.memoryUsage.toFixed(1)}%`,
      icon: HardDrive,
      status: healthData.memoryUsage < 80 ? 'healthy' : 'warning',
      format: 'percentage',
      rawValue: healthData.memoryUsage
    },
    {
      title: 'Model Version',
      value: healthData.modelVersion,
      icon: Database,
      status: 'operational',
      format: 'text'
    },
    {
      title: 'Uptime',
      value: healthData.uptime,
      icon: Clock,
      status: 'operational',
      format: 'text'
    },
    {
      title: 'Queue Length',
      value: healthData.queueLength,
      icon: Activity,
      status: healthData.queueLength < 10 ? 'healthy' : 'warning',
      format: 'number'
    },
    {
      title: 'Analyses Completed',
      value: healthData.analysesCompleted.toLocaleString(),
      icon: CheckCircle,
      status: 'operational',
      format: 'number'
    },
    {
      title: 'Avg Response Time',
      value: `${healthData.avgResponseTime}s`,
      icon: Zap,
      status: healthData.avgResponseTime < 2 ? 'healthy' : 'warning',
      format: 'text'
    },
    {
      title: 'Accuracy',
      value: `${healthData.accuracy}%`,
      icon: Shield,
      status: 'operational',
      format: 'percentage',
      rawValue: healthData.accuracy
    }
  ];

  return (
    <div className="min-h-screen pt-24 px-4 pb-12 bg-background">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl md:text-4xl font-bold font-display text-text-primary">System Health Dashboard</h1>
            <div className="flex items-center gap-2 text-text-secondary text-sm">
              <Activity className="w-4 h-4" />
              <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
            </div>
          </div>
          <p className="text-text-secondary">Real-time system metrics and health monitoring</p>
        </motion.div>

        {/* Status Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 p-6 bg-glass rounded-2xl border border-card/50"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                healthData.backendStatus === 'operational' ? 'bg-success/20' : 'bg-warning/20'
              }`}>
                {getStatusIcon(healthData.backendStatus)}
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-primary">System Status</h2>
                <p className={`text-sm font-medium ${getStatusColor(healthData.backendStatus)}`}>
                  {healthData.backendStatus.charAt(0).toUpperCase() + healthData.backendStatus.slice(1)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-text-secondary text-sm">Overall Health Score</p>
              <p className="text-2xl font-bold text-success">98%</p>
            </div>
          </div>
        </motion.div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {metrics.map((metric, index) => {
            const Icon = metric.icon;
            return (
              <motion.div
                key={metric.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + index * 0.05 }}
                className="p-6 bg-glass rounded-2xl border border-card/50 hover:border-accent/50 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    metric.status === 'healthy' || metric.status === 'operational' ? 'bg-success/20' : 'bg-warning/20'
                  }`}>
                    <Icon className={`w-5 h-5 ${getStatusColor(metric.status)}`} />
                  </div>
                  {getStatusIcon(metric.status)}
                </div>
                <p className="text-text-secondary text-sm mb-1">{metric.title}</p>
                <p className={`text-2xl font-bold ${
                  metric.format === 'percentage' && metric.rawValue ? getUsageColor(metric.rawValue) : 'text-text-primary'
                }`}>
                  {metric.value}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* Additional Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="mt-8 p-6 bg-glass rounded-2xl border border-card/50"
        >
          <h3 className="text-lg font-bold text-text-primary mb-4">System Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">Platform</span>
              <span className="text-text-primary">TruthLens Enterprise</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Environment</span>
              <span className="text-text-primary">Production</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Region</span>
              <span className="text-text-primary">US-East</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Python Version</span>
              <span className="text-text-primary">3.10.12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Framework</span>
              <span className="text-text-primary">FastAPI 0.104.1</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Database</span>
              <span className="text-text-primary">PostgreSQL 15</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default SystemHealth;
