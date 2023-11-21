<script lang="ts">
	import { onMount } from "svelte";
	import welcome from "$lib/images/svelte-welcome.webp";
	import welcome_fallback from "$lib/images/svelte-welcome.png";

	import { aqueductUrl, mcpUrl, deviceUrl } from "../stores";

	type HealthStatus = "Checking..." | "OK" | "Not OK" | "Error";

	let localDeviceUrl = $deviceUrl; // Initialize with store value

	let localUrls: Record<string, string> = {
		aqueduct: `http://${localDeviceUrl}:8888`,
		mcp: `http://${localDeviceUrl}:9097`,
	};

	onMount(() => {
		Object.keys(localUrls).forEach((key) => {
			checkHealth(key, localUrls[key]);

		});
		aqueductUrl.set(localUrls.aqueduct);
		mcpUrl.set(localUrls.mcp);
		if (localDeviceUrl == "" ) localDeviceUrl = window.location.hostname;
	});

	let healthStatuses: Record<string, HealthStatus> = {
		aqueduct: "Checking...",
		mcp: "Checking...",
	};

	async function checkHealth(key: string, url: string) {
		try {
			const res = await fetch(`${url}/health`, {
				method: "GET",
			});
			if (res.status === 200) {
				healthStatuses[key] = "OK";
			} else {
				healthStatuses[key] = "Not OK";
				console.error(`${key} Health status error:`, res);
			}
		} catch (error) {
			healthStatuses[key] = "Error";
			console.error(`${key} Health error:`, error);
		}
	}

	$: localUrls = {
		aqueduct: `http://${localDeviceUrl}:8888`,
		mcp: `http://${localDeviceUrl}:9097`,
	};

	$: {
		Object.keys(localUrls).forEach((key) => {
			checkHealth(key, localUrls[key]);
		});
		aqueductUrl.set(localUrls.aqueduct);
		mcpUrl.set(localUrls.mcp);
	}

	$: deviceUrl.set(localDeviceUrl);

</script>

<svelte:head>
	<title>Home</title>
	<meta name="description" content="Aqueduct demo app" />
</svelte:head>

<section>
	<h1>
		<span class="welcome">
			<picture>
				<source srcset={welcome} type="image/webp" />
				<img src={welcome_fallback} alt="Welcome" />
			</picture>
		</span>
	</h1>

	<div>
		<label for="deviceip" class="text-lg font-medium"
			>Enter Device IP:</label
		>
	</div>
	<input
		type="text"
		id="deviceip"
		bind:value={localDeviceUrl}
		class="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
	/>

	{#each Object.keys(localUrls) as key}
		
		<div>
			<label
				for={key}
				class={healthStatuses[key] === "OK"
					? "text-green-500"
					: healthStatuses[key] === "Not OK"
					? "text-yellow-500"
					: healthStatuses[key] === "Error"
					? "text-red-500"
					: "text-gray-500"}
				>{key.toUpperCase()} API Health: {healthStatuses[key]}</label
			>
		</div>
	{/each}
</section>

<style>
	section {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}

	h1 {
		width: 100%;
	}

	.welcome {
		display: block;
		position: relative;
		width: 100%;
		height: 0;
		padding: 0 0 calc(100% * 495 / 2048) 0;
	}

	.welcome img {
		position: absolute;
		width: 100%;
		height: 100%;
		top: 0;
		display: block;
	}
</style>
