<script lang="ts">
    import { onMount } from "svelte";
    import { pipelines } from "../../stores";

    export let aqueductUrl = "";
    let refreshRate = 10; // default rate in seconds
    let intervalId: number | undefined = undefined;
    let errorMessage = "";

    const fetchData = async () => {
        try {
            const response = await fetch(aqueductUrl + "/pipelines/status");
            if (response.ok) {
                const statusData = await response.json();
                pipelines.set(statusData);
                errorMessage = "";
            } else {
                errorMessage =
                    "Failed to fetch status from Aqueduct API: '" +
                    aqueductUrl +
                    "' . Status code: " +
                    response.status;
                console.error(errorMessage);
            }
        } catch (error) {
            errorMessage = "An error occurred while fetching data";
            console.error("Error:", error);
        }
    };

    const stopPipeline = async (sourceId: string) => {
        const payload = { sourceId };
        try {
            const response = await fetch(aqueductUrl + "/pipelines/stop", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                console.log("Pipeline stopped successfully");
            } else {
                console.error("Failed to stop pipeline:", response.status);
            }
        } catch (error) {
            console.error(
                "An error occurred while stopping the pipeline:",
                error
            );
        }
    };

    const deletePipeline = async (sourceId: string) => {
        const payload = { sourceId };
        try {
            const response = await fetch(aqueductUrl + "/pipelines/delete", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                console.log("Pipeline deleted successfully");
            } else {
                console.error("Failed to delete pipeline:", response.status);
            }
        } catch (error) {
            console.error(
                "An error occurred while stopping the pipeline:",
                error
            );
        }
    };

    function timeSince(timestamp: number): string {
        const now = Math.floor(Date.now() / 1000); // Current time in Unix timestamp (seconds)
        const secondsPast = now - timestamp;

        if (secondsPast < 60) {
            return `${secondsPast} seconds ago`;
        }

        const minutesPast = Math.floor(secondsPast / 60);
        if (minutesPast < 60) {
            return `${minutesPast} minutes ago`;
        }

        const hoursPast = Math.floor(minutesPast / 60);
        if (hoursPast < 24) {
            return `${hoursPast} hours ago`;
        }

        const daysPast = Math.floor(hoursPast / 24);
        return `${daysPast} days ago`;
    }

    onMount(() => {
        fetchData();
        intervalId = setInterval(fetchData, refreshRate * 1000);
    });

    $: {
        clearInterval(intervalId);
        intervalId = setInterval(fetchData, refreshRate * 1000);
    }
</script>

<div>
    <label
        class="block mb-2 text-sm font-medium text-gray-800"
        for="refreshRate"
        >Refresh rate (in seconds):
    </label>
    <input
        class="bg-gray-50 border border-gray-300 text-gray-800 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
        id="refreshRate"
        type="number"
        bind:value={refreshRate}
        min="1"
    />

    {#if errorMessage}
        <div class="error">{errorMessage}</div>
    {/if}

    <h1
        class="mb-4 text-xl font-extrabold leading-none tracking-tight text-gray-700 md:text-5xl lg:text-2xl"
    >
        List of Pipelines
    </h1>
    {#if $pipelines}
        <div class="relative overflow-x-auto">
            <table
                class="w-full text-sm text-left text-gray-500 dark:text-gray-400"
            >
                <thead
                    class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400"
                >
                    <tr>
                        <th scope="col" class="px-6 py-3">Source ID</th>
                        <th scope="col" class="px-6 py-3">URL</th>
                        <th scope="col" class="px-6 py-3">Status</th>
                        <th scope="col" class="px-6 py-3">Last Update</th>
                        <th scope="col" class="px-6 py-3">Action</th>
                        <th scope="col" class="px-6 py-3">Delete</th>
                    </tr>
                </thead>
                <tbody>
                    {#each Object.keys($pipelines) as sourceId}
                        <tr
                            class="bg-white border-b dark:bg-gray-800 dark:border-gray-700"
                        >
                            <td class="px-6 py-4">{sourceId}</td>
                            <td class="px-6 py-4"
                                >{$pipelines[sourceId].data.parameters
                                    .VIDEO_IN}</td
                            >
                            <td class="px-6 py-4"
                                >{$pipelines[sourceId].status}</td
                            >
                            <td class="px-6 py-4"
                                >{timeSince(
                                    $pipelines[sourceId].lastUpdate
                                )}</td
                            >
                            <td class="px-6 py-4">
                                <button
                                    class="focus:outline-none text-white bg-red-700 hover:bg-red-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900"
                                    on:click={() => stopPipeline(sourceId)}
                                    >Stop Pipeline</button
                                >
                            </td>
                            <td class="px-6 py-4">
                                <button
                                    class="focus:outline-none text-white bg-red-700 hover:bg-red-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900"
                                    on:click={() => deletePipeline(sourceId)}
                                    >Delete Pipeline</button
                                >
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>

<style>
    .error {
        color: red;
    }
</style>
