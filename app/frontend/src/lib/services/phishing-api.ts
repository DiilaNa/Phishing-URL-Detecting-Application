import type {
	BatchPredictionResponse,
	HealthStatus,
	HistoryResponse,
	ModelInfo,
	PredictionResult
} from '$lib/types/phishing';

const API_URL = 'http://127.0.0.1:8000';

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		let message = 'Something went wrong while communicating with the server.';

		try {
			const error = await response.json();
			message = error.detail || message;
		} catch {
			// Keep default message
		}

		throw new Error(message);
	}

	return response.json();
}

export async function checkHealth(): Promise<HealthStatus> {
	const response = await fetch(`${API_URL}/`);

	return handleResponse<HealthStatus>(response);
}

export async function predictUrl(url: string): Promise<PredictionResult> {
	const response = await fetch(`${API_URL}/predict`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			url
		})
	});

	return handleResponse<PredictionResult>(response);
}

export async function predictBatch(urls: string[]): Promise<BatchPredictionResponse> {
	const response = await fetch(`${API_URL}/predict-batch`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			urls
		})
	});

	return handleResponse<BatchPredictionResponse>(response);
}

export async function getModelInfo(): Promise<ModelInfo> {
	const response = await fetch(`${API_URL}/model-info`);

	return handleResponse<ModelInfo>(response);
}

export async function getHistory(): Promise<HistoryResponse> {
	const response = await fetch(`${API_URL}/history`);

	return handleResponse<HistoryResponse>(response);
}