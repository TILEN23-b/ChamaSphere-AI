document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const wrapper = button.closest(".input-wrap");
            const input = wrapper ? wrapper.querySelector("input") : null;
            if (!input) return;

            const visible = input.type === "text";
            input.type = visible ? "password" : "text";

            button.innerHTML = visible
                ? '<i class="bi bi-eye"></i>'
                : '<i class="bi bi-eye-slash"></i>';

            button.setAttribute(
                "aria-label",
                visible ? "Show password" : "Hide password"
            );
        });
    });

    document.querySelectorAll(".premium-input").forEach((input) => {
        input.addEventListener("focus", () => input.closest(".input-wrap")?.classList.add("focused"));
        input.addEventListener("blur", () => input.closest(".input-wrap")?.classList.remove("focused"));
    });
});
