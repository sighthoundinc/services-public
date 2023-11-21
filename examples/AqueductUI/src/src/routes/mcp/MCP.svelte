<script lang="ts">
    import { onMount } from "svelte";
    import Hls from "hls.js";

    export let mcpUrl = "";
    let refreshRate = 10; // Refresh rate in seconds
    let intervalId: number | undefined; // For setting intervals
    let errorMessage = ""; // To store any errors
    let sourceStats: Record<string, any> = {}; // To store the fetched source statistics

    let currentHlsInstance: Hls | null = null; // To store the current Hls instance
    let displayHls: boolean = false; // To display the Hls instance

    // Fetch basic list of sources and then their details
    const fetchData = async () => {
        try {
            // Fetch list of sources
            const response = await fetch(`${mcpUrl}/hlsfs/source`, {});
            if (response.status === 401 || response.status === 0) {
                errorMessage = "Unauthorized, please set username and password";
            } else if (response.ok) {
                const sourceList: string[] = await response.json();

                // Fetch detailed stats for each source
                for (const sourceId of sourceList) {
                    const statsResponse = await fetch(
                        `${mcpUrl}/hlsfs/source/${sourceId}/stats`,
                        {}
                    );
                    if (statsResponse.ok) {
                        const statsData = await statsResponse.json();
                        sourceStats[sourceId] = statsData;
                    } else {
                        errorMessage = `Failed to fetch stats for source ${sourceId}: ${statsResponse.status}`;
                    }
                }

                errorMessage = "";
            } else {
                errorMessage = `Failed to fetch from MCP API: ${response.status}`;
            }
        } catch (error) {
            errorMessage = "An error occurred while fetching data";
            console.error("MCP fetch error:", mcpUrl, error);
        }
    };

    // Function to delete a source
    const deleteSource = async (sourceId: string) => {
        try {
            const response = await fetch(`${mcpUrl}/hlsfs/source/${sourceId}`, {
                method: "DELETE"
            });

            if (response.ok) {
                // Remove the deleted source from sourceStats
                delete sourceStats[sourceId];
            } else {
                errorMessage = `Failed to delete source ${sourceId}: ${response.status}`;
            }
        } catch (error) {
            errorMessage = "An error occurred while deleting the source";
            console.error("Delete source error:", mcpUrl, error);
        }
    };

    const startLiveView = (sourceId: string) => {
        displayHls = true;
        const videoElement = document.getElementById(
            `single-live-view`
        ) as HTMLVideoElement;

        // Stop any existing live view
        if (currentHlsInstance) {
            currentHlsInstance.destroy();
        }

        console.log("Starting live view for source:", sourceId);
        if (Hls.isSupported() && videoElement) {
            const hls = new Hls();
            hls.loadSource(`${mcpUrl}/hlsfs/source/${sourceId}/live`);
            hls.attachMedia(videoElement);
            hls.on(Hls.Events.MANIFEST_PARSED, function () {
                videoElement.play();
            });
            currentHlsInstance = hls;
        }
        console.log("Live view started");
    };

    const stopLiveView = () => {
        displayHls = false;
        if (currentHlsInstance) {
            currentHlsInstance.destroy();
            currentHlsInstance = null;
        }
    };

    function formatBytes(bytes: number, decimals = 1) {
        if (!+bytes) return "0 Bytes";

        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = [
            "Bytes",
            "KiB",
            "MiB",
            "GiB",
            "TiB",
            "PiB",
            "EiB",
            "ZiB",
            "YiB",
        ];

        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${
            sizes[i]
        }`;
    }

    // Initial fetch and setting the interval for fetching
    onMount(() => {
        fetchData();
        intervalId = setInterval(fetchData, refreshRate * 1000);
    });

    // Clear and re-set the interval whenever refreshRate changes
    $: {
        clearInterval(intervalId);
        intervalId = setInterval(fetchData, refreshRate * 1000);
    }
</script>

<div>
    <h2 class="text-xl font-extrabold">
        Connecting to MCP server: {mcpUrl}
    </h2>

    <label
        class="block mb-2 text-sm font-medium text-gray-800"
        for="refreshRate"
        >Refresh rate (in seconds):
    </label>
    <input
        class="bg-gray-50 border border-gray-300 text-gray-800 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500"
        id="refreshRate"
        type="number"
        bind:value={refreshRate}
        min="1"
    />
    <!-- 
    <label
        class="block mb-2 text-sm font-medium text-gray-800 "
        for="username"
        >Username
    </label>
    <input
        class="bg-gray-50 border border-gray-300 text-gray-800 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
        id="username"
        bind:value={username}
    />

    <label
        class="block mb-2 text-sm font-medium text-gray-800 "
        for="password"
        >Password
    </label>
    <input
        class="bg-gray-50 border border-gray-300 text-gray-800 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400  dark:focus:ring-blue-500 dark:focus:border-blue-500"
        id="password"
        bind:value={password}
        type="password"
    /> -->

    {#if errorMessage}
        <div class="error">{errorMessage}</div>
    {/if}

    <h1
        class="mb-4 text-xl font-extrabold leading-none tracking-tight text-gray-700 md:text-5xl lg:text-2xl"
    >
        List of MCP Sources
    </h1>

    {#if Object.keys(sourceStats).length}
        <div class="relative overflow-x-auto">
            <table
                class="w-full text-sm text-left text-gray-500 dark:text-gray-400"
            >
                <thead
                    class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400"
                >
                    <tr>
                        <th scope="col" class="px-6 py-3">Source ID</th>
                        <th scope="col" class="px-6 py-3">Number of Images</th>
                        <th scope="col" class="px-6 py-3">Number of Videos</th>
                        <th scope="col" class="px-6 py-3">Size</th>
                        <th scope="col" class="px-6 py-3">Latest Image</th>
                        <th scope="col" class="px-6 py-3">Live View</th>
                        <th scope="col" class="px-6 py-3">Delete source</th>
                    </tr>
                </thead>
                <tbody>
                    {#each Object.keys(sourceStats) as sourceId}
                        <tr
                            class="bg-white border-b dark:bg-gray-800 dark:border-gray-700"
                        >
                            <td class="px-6 py-4">{sourceId}</td>
                            <td class="px-6 py-4"
                                >{sourceStats[sourceId].numberOfImages}</td
                            >
                            <td class="px-6 py-4"
                                >{sourceStats[sourceId].numberOfVideos}</td
                            >
                            <td class="px-6 py-4"
                                >{formatBytes(sourceStats[sourceId].fileSize)}</td
                            >
                            <td class="px-6 py-4">
                                {#if sourceStats[sourceId].numberOfImages !== 0}
                                    <a
                                        href={`${mcpUrl}/hlsfs/source/${sourceId}/latest-image`}
                                        target="_blank"
                                        rel="noopener noreferrer">View</a
                                    >
                                {/if}
                            </td>
                            <td class="px-6 py-4">
                                {#if sourceStats[sourceId].numberOfVideos !== 0}
                                    <button
                                        class="focus:outline-none text-white bg-green-700 hover:bg-green-800 focus:ring-4 focus:ring-green-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-800"
                                        on:click={() => startLiveView(sourceId)}
                                    >
                                        Start
                                    </button>
                                {/if}
                            </td>
                            <td class="px-6 py-4">
                                <button
                                    class="focus:outline-none text-white bg-red-700 hover:bg-red-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900"
                                    on:click={() => deleteSource(sourceId)}
                                >
                                    Delete
                                </button>
                            </td></tr
                        >
                    {/each}
                </tbody>
            </table>
        </div>
    {:else}
        <div class="text-gray-500 dark:text-gray-400">No sources found</div>
    {/if}
</div>

<br />
{#if displayHls}
    <h1
        class="mb-4 text-xl font-extrabold leading-none tracking-tight text-gray-700 md:text-5xl lg:text-2xl"
    >
        Live view
    </h1>

    <!-- Single video element for live view -->
    <video id="single-live-view" controls>
        <track kind="captions" />
    </video>
    <br />
    <button
        class="focus:outline-none text-white bg-red-700 hover:bg-red-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900"
        on:click={stopLiveView}>Stop</button
    >
{/if}

<style>
    .error {
        color: red;
    }
    /* Add more styling as needed */
</style>
