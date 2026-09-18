export interface PredictionResult {
	url: string;
	is_phishing: boolean;
	status: string;
	risk_score_percentage: number;
	features: Record<string, number>;
	timestamp: string;
}

export interface HealthStatus {
	status: string;
	model_loaded: boolean;
	algorithm: string;
	features_count: number;
}

export interface ModelInfo {
	model_name: string;
	benchmark_test_accuracy: string;
	benchmark_f1_score: string;
	total_features: number;
	feature_names: string[];
	feature_importance_weights: Record<string, number>;
	estimators_count: number;
}

export interface HistoryItem {
	url: string;
	status: string;
	risk: number;
	timestamp: string;
}

export interface HistoryResponse {
	count: number;
	recent_scans: HistoryItem[];
}

export interface BatchPredictionResponse {
	total_analyzed: number;
	results: PredictionResult[];
}