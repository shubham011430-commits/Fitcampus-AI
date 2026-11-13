let currentMealFilter = "all";
let menuType = "college_canteen";

document.addEventListener("DOMContentLoaded", async () => {
    Auth.requireAuth();
    const user = API.getUser() || await Auth.refreshUser();
    if (user) {
        renderProfileChip(user);
        // Set menu type based on student type
        menuType = user.student_type === "hosteler" ? "hostel_mess" : "college_canteen";
        const title = user.student_type === "hosteler" ? "🏠 Hostel Mess Menu" : "🎒 College Canteen Menu";
        document.getElementById("menuTitle").textContent = title;
    }
    document.getElementById("logoutBtn")?.addEventListener("click", Auth.logout);

    document.querySelectorAll(".menu-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".menu-tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentMealFilter = tab.dataset.meal;
            loadMenu();
        });
    });

    await loadMenu();
});

async function loadMenu() {
    const host = document.getElementById("menuContent");
    if (!host) return;
    host.innerHTML = '<div class="loader"></div>';

    try {
        let url = "/api/menu/my-menu";
        if (currentMealFilter !== "all") {
            url += `?meal_type=${currentMealFilter}`;
        }
        const items = await API.get(url);

        if (!items.length) {
            host.innerHTML = `<div class="empty-state"><div class="ico">🍽️</div>No menu items available for this selection.</div>`;
            return;
        }

        // Group by meal type
        const grouped = {};
        items.forEach(item => {
            if (!grouped[item.meal_type]) grouped[item.meal_type] = [];
            grouped[item.meal_type].push(item);
        });

        const mealOrder = ["breakfast", "lunch", "snacks", "dinner"];
        const mealIcons = { breakfast: "🌅", lunch: "☀️", snacks: "🍿", dinner: "🌙" };
        const mealNames = { breakfast: "Breakfast", lunch: "Lunch", snacks: "Evening Snacks", dinner: "Dinner" };

        let html = "";
        mealOrder.forEach(meal => {
            if (grouped[meal]) {
                const timing = grouped[meal][0].timing || "";
                html += `
                    <div class="menu-section">
                        <div class="menu-section-title">${mealIcons[meal]} ${mealNames[meal]}</div>
                        ${timing ? `<div class="menu-section-timing">⏰ ${timing}</div>` : ''}
                        ${grouped[meal].map(item => menuItemHTML(item)).join("")}
                    </div>
                `;
            }
        });
        host.innerHTML = html;
    } catch (e) {
        host.innerHTML = `<div class="empty-state">Failed to load menu: ${e.message}</div>`;
    }
}

function menuItemHTML(item) {
    const categoryBadge = item.category === "non_veg"
        ? '<span class="menu-item-badge badge-nonveg">NON-VEG</span>'
        : item.category === "vegan"
        ? '<span class="menu-item-badge badge-vegan">VEGAN</span>'
        : '<span class="menu-item-badge badge-veg">VEG</span>';

    const priceTag = item.price != null ? `<div class="menu-item-price">₹${item.price}</div>` : '';

    const meta = [];
    if (item.calories != null) meta.push(`<span>🔥 ${item.calories} kcal</span>`);
    if (item.protein_g != null) meta.push(`<span>💪 ${item.protein_g}g protein</span>`);
    if (item.carbs_g != null) meta.push(`<span>🌾 ${item.carbs_g}g carbs</span>`);
    if (item.fat_g != null) meta.push(`<span>🥑 ${item.fat_g}g fat</span>`);
    if (item.allergens && item.allergens.length) {
        meta.push(`<span style="color:var(--red-500);">⚠️ ${item.allergens.join(", ")}</span>`);
    }

    return `
        <div class="menu-item">
            <div>
                <div class="menu-item-name">${item.name}${categoryBadge}</div>
                ${item.description ? `<div style="font-size:12px; color:var(--gray-500); margin-top:2px;">${item.description}</div>` : ''}
                <div class="menu-item-meta">${meta.join("")}</div>
            </div>
            ${priceTag}
        </div>
    `;
}