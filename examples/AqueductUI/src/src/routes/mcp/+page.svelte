<script>
	import MCP from './MCP.svelte';
	import { mcpUrl } from '../../stores';

</script>

<svelte:head>
	<title>Pipelines</title>
	<meta name="description" content="Pipelines" />
</svelte:head>

<div class="text-column">
	<h1 class="mb-4 text-2xl font-extrabold leading-none tracking-tight text-gray-800 md:text-5xl lg:text-4xl ">Media Control Plane</h1>
</div>

<MCP mcpUrl={$mcpUrl} />

