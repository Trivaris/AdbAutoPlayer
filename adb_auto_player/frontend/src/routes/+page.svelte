<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import CommandPanel from "./CommandPanel.svelte";
  import ConfigForm from "./ConfigForm.svelte";
  import LogDisplay from "./LogDisplay.svelte";
  import Menu from "./Menu.svelte";

  let disableActions: boolean = $state(false);
  $effect(() => {
    window.imageIsActive(!disableActions);
  });
  let game: string | null = $state(null);
  let buttons: Button[] = $state([]);
  let configFormProps: Record<string, any> = $state({});
  let isGameConfig: boolean = $state(false);
  let showConfigForm: boolean = $state(false);
  let log: string[] = $state([]);

  const defaultButtons: Button[] = [
    {
      label: "Edit Main Config",
      callback: () => openConfigForm({ openGameConfig: false }),
      active: false,
    },
  ];

  function append_to_log(message: string) {
    log.push(message);
  }
  window.eel.expose(append_to_log);

  function updateMenu() {
    window.eel.get_menu()((response: string[] | null) => {
      if (response !== null) {
        buttons = response.map((label, index) => ({
          label: label,
          callback: () => executeMenuItem(index),
          active: false,
        }));
        buttons.push(
          {
            label: "Edit Game Config",
            callback: () => openConfigForm({ openGameConfig: true }),
            active: false,
          },
          {
            label: "Stop Action",
            callback: () => window.eel.stop_action(),
            active: false,
            alwaysEnabled: true,
          },
        );
      } else {
        buttons = [];
      }
    });
  }

  function executeMenuItem(actionIndex: number): void {
    if (buttons) {
      buttons = buttons.map((button, i) => ({
        ...button,
        active: i === actionIndex,
      }));
    }
    disableActions = true;
    window.eel.execute(actionIndex);
  }

  function openConfigForm({ openGameConfig }: { openGameConfig: boolean }) {
    isGameConfig = openGameConfig;
    showConfigForm = true;
    window.eel.get_editable_config(isGameConfig)((response: any) => {
      configFormProps = response;
    });
  }

  function onConfigSave() {
    showConfigForm = false;
  }

  let updateStateTimeout: number | undefined;
  function updateState() {
    console.log("updateState");
    console.log(showConfigForm);
    console.log(disableActions);
    if (showConfigForm) {
      updateStateTimeout = setTimeout(updateState, 2500);
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
    updateStateTimeout = setTimeout(updateState, 2500);
  }

  onMount(() => {
    updateState()
  });

  onDestroy(() => {
    clearTimeout(updateStateTimeout);
  });
</script>

<main class="container">
  <h1>{game ? game : "Please start a supported game"}</h1>

  {#if showConfigForm}
    <ConfigForm
      config={configFormProps.config ?? []}
      constraints={configFormProps.constraints ?? []}
      {onConfigSave}
      {isGameConfig}
    />
  {:else}
    <CommandPanel title={"Menu"}>
      <Menu {buttons} {defaultButtons} {disableActions}></Menu>
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
</style>
