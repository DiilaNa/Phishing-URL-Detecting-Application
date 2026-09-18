<script lang="ts">
	import type { HistoryItem } from '$lib/types/phishing';

	let { history }: { history: HistoryItem[] } = $props();
</script>

<section class="panel">

	<div class="panel-header">
		<div>
			<h3>Recent Scans</h3>
			<p>Latest URLs analyzed by the system</p>
		</div>

		<span class="count">{history.length}</span>
	</div>

	{#if history.length === 0}

		<div class="empty">
			<div>🕘</div>
			<p>No scans yet</p>
		</div>

	{:else}

		<div class="history-list">

			{#each history as item}
				<div class="history-item">

					<div
						class:danger={item.status.includes('Phishing')}
						class:safe={!item.status.includes('Phishing')}
						class="history-icon"
					>
						{item.status.includes('Phishing') ? '!' : '✓'}
					</div>

					<div class="history-content">
						<div class="history-url">{item.url}</div>
						<div class="history-time">{item.timestamp}</div>
					</div>

					<div
						class:danger-text={item.status.includes('Phishing')}
						class:safe-text={!item.status.includes('Phishing')}
						class="history-risk"
					>
						{item.risk}%
					</div>

				</div>
			{/each}

		</div>

	{/if}

</section>

<style>
	.panel {
		background: #111827;
		border: 1px solid #1e293b;
		border-radius: 18px;
		padding: 22px;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 18px;
	}

	h3 {
		margin: 0;
		color: #f1f5f9;
		font-size: 16px;
	}

	.panel-header p {
		margin: 4px 0 0;
		color: #64748b;
		font-size: 12px;
	}

	.count {
		display: grid;
		place-items: center;
		min-width: 28px;
		height: 28px;
		border-radius: 8px;
		background: #1e293b;
		color: #94a3b8;
		font-size: 12px;
	}

	.history-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.history-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 12px;
		border-radius: 10px;
		background: #0f172a;
	}

	.history-icon {
		flex: 0 0 auto;
		width: 28px;
		height: 28px;
		display: grid;
		place-items: center;
		border-radius: 50%;
		font-size: 13px;
		font-weight: bold;
	}

	.history-icon.safe {
		background: rgba(34, 197, 94, 0.1);
		color: #4ade80;
	}

	.history-icon.danger {
		background: rgba(239, 68, 68, 0.1);
		color: #f87171;
	}

	.history-content {
		min-width: 0;
		flex: 1;
	}

	.history-url {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: #cbd5e1;
		font-size: 13px;
	}

	.history-time {
		margin-top: 3px;
		color: #475569;
		font-size: 10px;
	}

	.history-risk {
		font-size: 12px;
		font-weight: 700;
	}

	.safe-text {
		color: #4ade80;
	}

	.danger-text {
		color: #f87171;
	}

	.empty {
		padding: 30px;
		text-align: center;
		color: #475569;
	}

	.empty div {
		font-size: 25px;
	}

	.empty p {
		font-size: 12px;
	}
</style>