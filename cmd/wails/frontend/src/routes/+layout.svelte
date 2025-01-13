<script lang="ts">
    import LogoSticky from "./LogoSticky.svelte";
    import DocumentationIconSticky from "./DocumentationIconSticky.svelte";

    let { children } = $props();
</script>

<DocumentationIconSticky></DocumentationIconSticky>
<LogoSticky></LogoSticky>

{@render children()}
