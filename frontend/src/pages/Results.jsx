import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import ConfidenceGauge from '../components/ConfidenceGauge';
import VerdictBadge from '../components/VerdictBadge';

const Results = () => {
  const location = useLocation();
  const { result, type } = location.state || {};

  if (!result) {
    return (
      <div className="min-h-screen bg-navy-900 bg-hex-pattern flex items-center justify-center">
        <div className="text-text-secondary">No results to display</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy-900 bg-hex-pattern">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-16">
        <h1 className="text-4xl font-heading font-bold text-text-primary mb-8">Analysis Results</h1>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-navy-800/50 backdrop-blur-lg border border-cyan-400/20 rounded-2xl p-8"
        >
          <div className="flex items-center justify-between mb-8">
            <VerdictBadge verdict={result.result} />
            <ConfidenceGauge value={result.confidence || result.authenticity_score} />
          </div>

          {result.reasons && (
            <div className="mb-6">
              <h3 className="text-lg font-heading font-semibold text-text-primary mb-3">Reasons</h3>
              <ul className="space-y-2">
                {result.reasons.map((reason, index) => (
                  <li key={index} className="flex items-start space-x-2 text-text-secondary">
                    <span className="text-cyan-400">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.issues && (
            <div className="mb-6">
              <h3 className="text-lg font-heading font-semibold text-text-primary mb-3">Issues Detected</h3>
              <ul className="space-y-2">
                {result.issues.map((issue, index) => (
                  <li key={index} className="flex items-start space-x-2 text-text-secondary">
                    <span className="text-danger">•</span>
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.sources && (
            <div>
              <h3 className="text-lg font-heading font-semibold text-text-primary mb-3">Sources</h3>
              <div className="space-y-2">
                {result.sources.map((source, index) => (
                  <a
                    key={index}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-3 bg-navy-900 rounded-lg hover:border-cyan-400 border border-transparent transition-colors"
                  >
                    <div className="text-text-primary font-medium">{source.name}</div>
                    <div className="text-sm text-text-secondary">Relevance: {Math.round((source.relevance || 0) * 100)}%</div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {result.suspicious_timestamps && (
            <div className="mt-6">
              <h3 className="text-lg font-heading font-semibold text-text-primary mb-3">Suspicious Timestamps</h3>
              <div className="flex flex-wrap gap-2">
                {result.suspicious_timestamps.map((timestamp, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-danger/20 text-danger rounded-full text-sm"
                  >
                    {timestamp}s
                  </span>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Results;
