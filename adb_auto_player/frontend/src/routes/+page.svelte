<script lang="ts">
  import { onMount } from "svelte";
  import CommandPanel from "./CommandPanel.svelte";
  import ConfigForm from "./ConfigForm.svelte";
  import LogDisplay from "./LogDisplay.svelte";

  let disableActions: boolean = $state(false);
  $effect(() => {
    window.imageIsActive(!disableActions);
  });
  let game: string | null = $state(null);
  let games: string[] | null = $state(null);
  let buttons: { label: string; index: number; active: boolean }[] = $state([]);
  let editableConfig: Record<string, any> = $state({});
  let configConstraints: Record<string, any> = $state({});
  let isGameConfig: boolean = $state(false);
  let showConfigForm: boolean = $state(false);
  let log: string[] = $state([]);

  function append_to_log(message: string) {
    log.push(message);
  }
  window.eel.expose(append_to_log);

  function updateMenu() {
    window.eel.get_menu()((response: string[] | null) => {
      if (JSON.stringify(games) !== JSON.stringify(response)) {
        games = response;

        buttons = [];

        if (games !== null) {
          buttons = games.map((gameName, index) => ({
            label: gameName,
            index,
            active: false,
          }));
        }
      }
    });
  }

  function updateState() {
    if (showConfigForm) {
      return;
    }
    if (disableActions) {
      window.eel.action_is_running()((response: boolean) => {
        disableActions = response;
      });
    } else {
      window.eel.get_running_supported_game()((response: null | string) => {
        if (game !== response) {
          game = response;
          updateMenu();
        }
      });
    }
  }

  onMount(() => {
    updateState();
    setInterval(updateState, 3000);
  });

  function executeMenuItem(event: Event, index: number) {
    event.preventDefault();
    if (buttons) {
      buttons = buttons.map((button, i) => ({
        ...button,
        active: i === index,
      }));
    }
    disableActions = true;
    window.eel.execute(index);
  }

  function stopAction(event: Event) {
    event.preventDefault();
    window.eel.stop_action();
  }

  function openConfigForm({ openGameConfig }: { openGameConfig: boolean }) {
    isGameConfig = openGameConfig;
    window.eel.get_editable_config(isGameConfig)((response: any) => {
      editableConfig = response.config;
      configConstraints = response.constraints;
      showConfigForm = true;
    });
  }

  function onConfigSave() {
    showConfigForm = false;
  }
</script>

<main class="container">
  <h1>{game ? game : "Please start a supported game"}</h1>

  {#if showConfigForm}
    <ConfigForm
      config={editableConfig}
      constraints={configConstraints}
      {onConfigSave}
      {isGameConfig}
    />
  {:else}
    <CommandPanel title={"Menu"}>
      {#if buttons.length > 0}
        {#each buttons as { label, index, active }}
          <button
            disabled={disableActions}
            class:active
            onclick={(event) => executeMenuItem(event, index)}
          >
            {label}
          </button>
        {/each}
        <button onclick={(event) => stopAction(event)}> Stop Action </button>
        <button
          disabled={disableActions}
          onclick={() => openConfigForm({ openGameConfig: true })}
        >
          Edit Game Config
        </button>
      {:else}
        <button
          disabled={disableActions}
          onclick={() => openConfigForm({ openGameConfig: false })}
        >
          Edit Main Config
        </button>
      {/if}
    </CommandPanel>
  {/if}

  <CommandPanel title={"Logs"}>
    <LogDisplay {log} />
  </CommandPanel>
</main>

<style>
  .container {
    margin: 0;
    padding-top: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
  }

  button {
    margin: 5px;
    padding: 10px 20px;
    font-size: 1em;
    cursor: pointer;
    border-radius: 5px;
    transition: background-color 0.2s ease-in-out;
  }

  button:disabled.active {
    opacity: 1;
    outline: 2px solid #396cd8;
  }

  button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
</style>
