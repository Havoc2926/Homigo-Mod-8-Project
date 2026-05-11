document.addEventListener("DOMContentLoaded", () => {
    const lightList = document.getElementById("light-list");

    let devices = [];

    // Fetch lights
    fetch("/lights")
        .then(res => res.json())
        .then(data => {
            devices = data;
            devices.forEach(device => {
                const li = document.createElement("li");
                li.textContent = `${device.name} (${device.device})`;
                lightList.appendChild(li);
            });
            return fetch("/api/scenes");
        })
        .then(res => res.json())
        .then(sceneData => {
            ["happy", "focus", "party"].forEach(scene => {
                const pickerDiv = document.querySelector(`.color-pickers[data-scene='${scene}']`);
                pickerDiv.innerHTML = '';
                devices.forEach(device => {
                    const input = document.createElement("input");
                    input.type = "color";
                    input.dataset.device = device.device;
                    input.value = sceneData[scene][device.device] ? `#${sceneData[scene][device.device]}` : "#ffffff";

                    pickerDiv.appendChild(input);
                });
            });
        });

    // Save Scene
    document.querySelectorAll(".save-scene").forEach(button => {
        button.addEventListener("click", () => {
            const scene = button.dataset.scene;
            const pickers = document.querySelectorAll(`.color-pickers[data-scene='${scene}'] input`);
            const colors = {};
            pickers.forEach(picker => {
                colors[picker.dataset.device] = picker.value.replace("#", "");
            });

            fetch("/api/scenes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: scene, colors })
            })
                .then(res => res.json())
                .then(data => alert(data.message || "Saved!"));
        });
    });

    // Trigger Scene
    document.querySelectorAll(".trigger-scene").forEach(button => {
        button.addEventListener("click", () => {
            const scene = button.dataset.scene;
            fetch(`/api/trigger/${scene}`)
                .then(res => res.json())
                .then(data => alert(data.message || "Triggered!"));
        });
    });
});
