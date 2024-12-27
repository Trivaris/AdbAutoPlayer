<script lang="ts">
  let {
    log,
  }: {
    log: string[];
  } = $props();

  let logContainer: HTMLDivElement;

  function getLogColor(message: string): string {
    if (message.includes("[DEBUG]")) return "cyan";
    if (message.includes("[INFO]")) return "green";
    if (message.includes("[WARNING]")) return "yellow";
    if (message.includes("[ERROR]")) return "red";
    if (message.includes("[CRITICAL]")) return "darkred";
    return "white";
  }
  $effect(() => {
    if (logContainer && log.length > 0) {
      requestAnimationFrame(() => {
        logContainer.scrollTop = logContainer.scrollHeight;
      });
    }
  });
</script>

<div class="log-container" bind:this={logContainer}>
  {#each log as message}
    <div style="color: {getLogColor(message)}">
      {message}
    </div>
  {/each}
</div>

<style>
  .log-container {
    height: 200px;
    overflow-y: auto;
    background-color: #0f0f0f98;
    padding: 10px;
    resize: vertical;
    white-space: pre-wrap;
    text-align: left;
    font-family: Consolas, monospace;
  }
</style>
