<script lang="ts">
	import { aqueductUrl } from "../../stores";
	import Modal from "../../components/Modal.svelte";
	let localaqueductUrl = $aqueductUrl; // Initialize with store value

	let sourceId = "";
	let pipeline = "";
	let URL = "";
	let loading = false;
	let showModal = false;
	let modalMessage = "";
	let extra_parameters = [] as { key: string; value: string }[];

	const startPipeline = async () => {
		if (!sourceId || !pipeline || !URL) {
			modalMessage = "All fields are required.";
			showModal = true;
			return;
		}

		// Convert extra_parameters array to object
		const extraParamsObject = {} as { [key: string]: string };
		for (const { key, value } of extra_parameters) {
			if (key) {
				extraParamsObject[key] = value;
			}
		}

		loading = true;
		try {
			const response = await fetch(
				`${localaqueductUrl}/pipelines/start`,
				{
					method: "POST",
					body: JSON.stringify({
						sourceId,
						pipeline,
						URL,
						extra_parameters: extraParamsObject,
					}),
					headers: {
						"Content-Type": "application/json",
					},
				}
			);

			if (response.ok) {
				modalMessage = "Pipeline started successfully.";
			} else {
				const responseBody = await response.json(); // Assuming API returns JSON
				const errorMsg = responseBody.message
					? responseBody.message
					: await response.text();
				modalMessage = `Error starting pipeline: ${errorMsg}`;
			}

			console.log("Pipeline start response:", response);
			showModal = true;
		} catch (error) {
			modalMessage = "Error starting pipeline. " + error;
			showModal = true;
			console.error("Error:", error);
		} finally {
			loading = false;
		}
	};

	function addExtraParam() {
		extra_parameters = [...extra_parameters, { key: "", value: "" }];
	}

	function removeExtraParam(index: number) {
		extra_parameters = extra_parameters.filter((_, i) => i !== index);
	}
</script>

<svelte:head>
	<title>start</title>
	<meta name="description" content="Start" />
</svelte:head>

<br />

<h2 class="text-5xl font-extrabold ">
	Starting an Aqueduct Pipeline
</h2>

<br />

<div>
	<label
		for="sourceId"
		class="block mb-2 text-sm font-medium text-gray-900 "
		>Source Identifier</label
	>
	<input
		id="sourceId"
		class="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
		placeholder="my-video"
		bind:value={sourceId}
	/>
	<label
		for="pipeline"
		class="block mb-2 text-sm font-medium text-gray-900 "
		>Pipeline</label
	>
	<select
		id="pipeline"
		placeholder="Pipeline"
		bind:value={pipeline}
		class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
	>
		<option selected>Choose a Pipeline</option>
		<option value="VehicleAnalytics">Vehicle Analytics (Only cars)</option>
		<option value="TrafficAnalytics"
			>Traffic Analytics (Cars and people)</option
		>
	</select>
	<label
		for="URL"
		class="block mb-2 text-sm font-medium text-gray-900 "
		>URL</label
	>
	<input
		id="URL"
		class="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
		placeholder="rtsp://live555/my-video.mkv"
		bind:value={URL}
	/>
	<br />
	<button
		type="button"
		class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800"
		on:click={startPipeline}
		hidden={loading}
		disabled={loading}
	>
		Start Pipeline
	</button>
	{#if loading}
		<div role="status">
			<svg
				aria-hidden="true"
				class="w-8 h-8 mr-2 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600"
				viewBox="0 0 100 101"
				fill="none"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
					fill="currentColor"
				/>
				<path
					d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
					fill="currentFill"
				/>
			</svg>
			<span class="sr-only">Loading...</span>
		</div>
	{/if}
</div>

<h3>Extra SIO Parameters</h3>
{#each extra_parameters as extra, index}
	<div>
		<br />
		<label
			for="key"
			class="block mb-2 text-sm font-medium text-gray-900 "
			>Key</label
		>
		<input
			id="key"
			class="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
			placeholder="Key"
			bind:value={extra_parameters[index].key}
		/>
		<label
			for="value"
			class="block mb-2 text-sm font-medium text-gray-900 "
			>Value</label
		>
		<input
			id="value"
			class="block w-full p-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 sm:text-xs focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
			placeholder="Value"
			bind:value={extra_parameters[index].value}
		/>
		<br />
		<button
			type="button"
			class="focus:outline-none text-white bg-red-700 hover:bg-red-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900"
			on:click={() => removeExtraParam(index)}>Remove</button
		>
	</div>
{/each}
<button
	type="button"
	class="py-2.5 px-5 mr-2 mb-2 text-sm font-medium text-gray-900 focus:outline-none bg-white rounded-lg border border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-4 focus:ring-gray-200 dark:focus:ring-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700"
	on:click={addExtraParam}>Add Extra Parameter</button
>

<Modal bind:showModal>
	<h2 class="text-5xl font-extrabold " slot="header">
		Message
	</h2>

	<p>{modalMessage}</p>
</Modal>
