<script lang="ts">
    import { onMount } from 'svelte';

    let {
        config,
        constraints,
        onConfigSave,
        isGameConfig,
    } = $props();

    const configSections : Array<Dictionary<any>> = Object.entries(config)
        .filter(([key]) => key !== 'plugin')
        .map(([sectionKey, sectionConfig]) => ({
            sectionKey,
            sectionConfig
        }));

    function getInputType(sectionKey: string, key: string): string {
        const constraint = constraints[sectionKey]?.[key];
        if (!constraint) return 'text';
        return constraint.type ?? 'text';
    }

    function groupOptionsByFirstLetter(options: string[]): Record<string, string[]> {
        return options.reduce((acc: Record<string, string[]>, option: string) => {
            const firstLetter = option.charAt(0).toUpperCase();
            if (!acc[firstLetter]) {
                acc[firstLetter] = [];
            }
            acc[firstLetter].push(option);
            return acc;
        }, {});
    }

    function handleSave() {
        const formElement = document.querySelector('form.config-form') as HTMLFormElement;

        if (!formElement.checkValidity()) {
            formElement.reportValidity()
            return;
        }

        const formData = new FormData(formElement);
        const newConfig: { [key: string]: Dictionary<any> } = JSON.parse(JSON.stringify(config));

        for (const [sectionKey, sectionConfig] of Object.entries(newConfig)) {
            if (sectionKey === 'plugin') continue;

            for (const key of Object.keys(sectionConfig)) {
                const inputName = `${sectionKey}-${key}`;
                const inputValues = formData.getAll(inputName);

                switch (typeof sectionConfig[key]) {
                    case 'boolean':
                        sectionConfig[key] = formData.has(inputName);
                        break;
                    case 'number':
                        sectionConfig[key] = Number(formData.get(inputName));
                        break;
                    case 'object':
                        if (Array.isArray(sectionConfig[key])) {
                            sectionConfig[key] = inputValues.map(String);
                        }
                        break;
                    default:
                        sectionConfig[key] = formData.get(inputName);
                        break;
                }
            }
        }

        window.eel.save_config(newConfig, isGameConfig);
        onConfigSave?.();
    }

    function formatSectionKey(sectionKey: string): string {
        const withSpaces = sectionKey.replace(/_/g, ' ');
        return withSpaces.replace(/\b\w/g, (match) => match.toUpperCase());
    }

    function setupRealTimeValidation() {
        const formElement = document.getElementById('config-form') as HTMLFormElement;
        if (!formElement) {
            console.error("Form element not found.");
            return;
        }
        const inputs = formElement.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                if (!input.checkValidity()) {
                    input.reportValidity();
                }
            });
        });
    }

    onMount(() => {
        setupRealTimeValidation();
    });
</script>

<form class="config-form" id="config-form">
    <h2>{#if isGameConfig}Edit Game Config{:else}Edit Main Config{/if}</h2>

    {#each configSections as { sectionKey, sectionConfig } }
        <fieldset>
            <legend>{formatSectionKey(sectionKey)}</legend>

            {#each Object.entries(sectionConfig) as [key, value]}
                <div class="form-group">
                    <div class="form-group-inner">
                        <label for="{sectionKey}-{key}">
                            {formatSectionKey(key)}
                        </label>

                        <div class="input-container">
                            {#if getInputType(sectionKey, key) === 'checkbox'}
                                <input
                                        type="checkbox"
                                        id="{sectionKey}-{key}"
                                        name="{sectionKey}-{key}"
                                        checked={Boolean(value)}
                                />
                            {:else if getInputType(sectionKey, key) === 'number'}
                                <input
                                        type="number"
                                        id="{sectionKey}-{key}"
                                        name="{sectionKey}-{key}"
                                        value={value}
                                        min={constraints[sectionKey]?.[key]?.minimum ?? 1}
                                        max={constraints[sectionKey]?.[key]?.maximum ?? 999}
                                />
                            {:else if getInputType(sectionKey, key) === 'multicheckbox'}
                                {@const groupedOptions = groupOptionsByFirstLetter(constraints[sectionKey]?.[key]?.choices || [])}
                                <div class="multicheckbox-grouped">
                                    {#each Object.entries(groupedOptions) as [letter, options] }
                                        <div class="letter-group">
                                            <div class="letter-header">{letter}</div>
                                            <div class="letter-options">
                                                {#each options as option}
                                                    <label class="checkbox-container">
                                                        <input
                                                                type="checkbox"
                                                                name="{sectionKey}-{key}"
                                                                value={option}
                                                                checked={Array.isArray(value) ? value.includes(option) : false}
                                                        />
                                                        {option}
                                                    </label>
                                                {/each}
                                            </div>
                                        </div>
                                    {/each}
                                </div>
                            {:else if getInputType(sectionKey, key) === 'select'}
                                <select
                                        id="{sectionKey}-{key}"
                                        name="{sectionKey}-{key}"
                                >
                                    {#each constraints[sectionKey]?.[key]?.choices as option}
                                        <option value={option} selected={value === option}>{option}</option>
                                    {/each}
                                </select>
                            {:else}
                                <input
                                        type="text"
                                        id="{sectionKey}-{key}"
                                        name="{sectionKey}-{key}"
                                        value={value}
                                />
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </fieldset>
        <br/>
    {/each}

    <button type="button" onclick={handleSave}>Save</button>
</form>

<style>
    .config-form {
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        margin-left: 1.5rem;
        margin-right: 1.5rem;
        background-color: rgba(31, 31, 31, 0.8);
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .form-group {
        margin-bottom: 15px;
    }

    .form-group-inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .form-group:not(:has(.multicheckbox-grouped)) .form-group-inner label {
        flex: 0 0 200px;
        margin-right: 10px;
        text-align: right;
    }

    .input-container {
        flex: 1;
        display: flex;
        align-items: center;
    }

    .input-container input:not([type="checkbox"]) {
        width: 100%;
    }

    .input-container select {
        width: 100%;
    }

    .input-container input[type="checkbox"] {
        margin: 2px;
    }

    .multicheckbox-grouped {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .letter-group {
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        padding: 5px;
    }

    .letter-header {
        font-weight: bold;
        margin-bottom: 5px;
        text-align: center;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 2px;
    }

    .letter-options {
        display: flex;
        flex-direction: column;
    }

    .checkbox-container {
        display: flex;
        align-items: center;
        margin: 2px 0;
    }
</style>
