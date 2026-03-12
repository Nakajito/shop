document.addEventListener('DOMContentLoaded', function () {

    // ========================================================
    // Auto-generate slug from title
    // ========================================================
    const titleField = document.getElementById('id_title');
    const slugField = document.getElementById('id_slug');

    if (titleField && slugField) {
        titleField.addEventListener('input', function () {
            if (!slugField.dataset.modified) {
                slugField.value = titleField.value
                    .toLowerCase()
                    .replace(/[^\w\s-]/g, '')
                    .replace(/[\s_]+/g, '-')
                    .replace(/-+/g, '-')
                    .trim();
            }
        });

        slugField.addEventListener('input', function () {
            slugField.dataset.modified = 'true';
        });
    }

    // ========================================================
    // Formset: add / remove rows
    // ========================================================
    function addFormsetRow(prefix) {
        const container = document.getElementById(prefix + '-container');
        const emptyForm = document.getElementById(prefix + '-empty-form');
        const totalForms = document.getElementById('id_' + prefix + '-TOTAL_FORMS');
        if (!container || !emptyForm || !totalForms) return;

        const formIdx = parseInt(totalForms.value);
        const newForm = emptyForm.cloneNode(true);

        newForm.removeAttribute('id');
        newForm.classList.remove('d-none');
        // Replace __prefix__ with the actual form index
        newForm.innerHTML = newForm.innerHTML.replace(/__prefix__/g, formIdx);

        // Insert before the hidden template
        container.insertBefore(newForm, emptyForm);
        totalForms.value = formIdx + 1;

        attachDeleteHandler(newForm);
    }

    const addImageBtn = document.getElementById('add-image-btn');
    if (addImageBtn) {
        addImageBtn.addEventListener('click', function () {
            addFormsetRow('images');
        });
    }

    const addVideoBtn = document.getElementById('add-video-btn');
    if (addVideoBtn) {
        addVideoBtn.addEventListener('click', function () {
            addFormsetRow('videos');
        });
    }

    function attachDeleteHandler(row) {
        const deleteBtn = row.querySelector('.delete-formset-row');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function () {
                const deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
                if (deleteCheckbox) {
                    // Existing saved row - mark for deletion
                    deleteCheckbox.checked = true;
                    row.classList.add('to-delete');
                    row.style.display = 'none';
                } else {
                    // New unsaved row - just remove from DOM
                    row.remove();
                }
            });
        }
    }

    document.querySelectorAll('.formset-row:not([id$="-empty-form"])').forEach(attachDeleteHandler);

    // ========================================================
    // Cover image preview
    // ========================================================
    const coverInput = document.getElementById('id_cover_image');
    if (coverInput) {
        coverInput.addEventListener('change', function () {
            const preview = document.getElementById('cover-preview');
            if (preview && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    preview.classList.remove('d-none');
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // ========================================================
    // AJAX: Create category
    // ========================================================
    const addCategoryBtn = document.getElementById('add-category-btn');
    const newCategoryInput = document.getElementById('new-category-input');
    const categoryFeedback = document.getElementById('category-feedback');

    if (addCategoryBtn && newCategoryInput) {
        addCategoryBtn.addEventListener('click', function () {
            const name = newCategoryInput.value.trim();
            if (!name) {
                categoryFeedback.innerHTML = '<span class="text-warning">Escribe un nombre.</span>';
                return;
            }

            addCategoryBtn.disabled = true;
            categoryFeedback.innerHTML = '<span class="text-muted">Creando...</span>';

            fetch(window.BLOG_AJAX_URLS.createCategory, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'name=' + encodeURIComponent(name),
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                addCategoryBtn.disabled = false;
                if (data.error) {
                    categoryFeedback.innerHTML = '<span class="text-danger">' + data.error + '</span>';
                    return;
                }

                // Add new option to select and select it
                const select = document.getElementById('id_category');
                if (select) {
                    // Check if option already exists
                    let exists = false;
                    for (let i = 0; i < select.options.length; i++) {
                        if (select.options[i].value === String(data.id)) {
                            select.options[i].selected = true;
                            exists = true;
                            break;
                        }
                    }
                    if (!exists) {
                        const option = new Option(data.name, data.id, true, true);
                        select.add(option);
                    }
                }

                newCategoryInput.value = '';
                if (data.exists) {
                    categoryFeedback.innerHTML = '<span class="text-info">Categor\u00eda ya exist\u00eda, seleccionada.</span>';
                } else {
                    categoryFeedback.innerHTML = '<span class="text-success">Categor\u00eda "' + data.name + '" creada.</span>';
                }
                setTimeout(function () { categoryFeedback.innerHTML = ''; }, 3000);
            })
            .catch(function () {
                addCategoryBtn.disabled = false;
                categoryFeedback.innerHTML = '<span class="text-danger">Error de conexi\u00f3n.</span>';
            });
        });

        // Allow Enter key
        newCategoryInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addCategoryBtn.click();
            }
        });
    }

    // ========================================================
    // AJAX: Create tag
    // ========================================================
    const addTagBtn = document.getElementById('add-tag-btn');
    const newTagInput = document.getElementById('new-tag-input');
    const tagFeedback = document.getElementById('tag-feedback');

    if (addTagBtn && newTagInput) {
        addTagBtn.addEventListener('click', function () {
            const name = newTagInput.value.trim();
            if (!name) {
                tagFeedback.innerHTML = '<span class="text-warning">Escribe un nombre.</span>';
                return;
            }

            addTagBtn.disabled = true;
            tagFeedback.innerHTML = '<span class="text-muted">Creando...</span>';

            fetch(window.BLOG_AJAX_URLS.createTag, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'name=' + encodeURIComponent(name),
            })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                addTagBtn.disabled = false;
                if (data.error) {
                    tagFeedback.innerHTML = '<span class="text-danger">' + data.error + '</span>';
                    return;
                }

                // Add new checkbox to tag list and check it
                const tagsList = document.getElementById('tags-list');
                if (tagsList) {
                    // Check if already exists
                    const existingCheckbox = tagsList.querySelector('input[value="' + data.id + '"]');
                    if (existingCheckbox) {
                        existingCheckbox.checked = true;
                    } else {
                        const li = document.createElement('li');
                        const label = document.createElement('label');
                        label.setAttribute('for', 'id_tags_' + data.id);

                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.name = 'tags';
                        checkbox.value = data.id;
                        checkbox.id = 'id_tags_' + data.id;
                        checkbox.checked = true;

                        label.appendChild(checkbox);
                        label.appendChild(document.createTextNode(' ' + data.name));
                        li.appendChild(label);

                        const ul = tagsList.querySelector('ul');
                        if (ul) {
                            ul.appendChild(li);
                        } else {
                            tagsList.appendChild(li);
                        }
                    }
                }

                newTagInput.value = '';
                if (data.exists) {
                    tagFeedback.innerHTML = '<span class="text-info">Tag ya exist\u00eda, seleccionado.</span>';
                } else {
                    tagFeedback.innerHTML = '<span class="text-success">Tag "' + data.name + '" creado.</span>';
                }
                setTimeout(function () { tagFeedback.innerHTML = ''; }, 3000);
            })
            .catch(function () {
                addTagBtn.disabled = false;
                tagFeedback.innerHTML = '<span class="text-danger">Error de conexi\u00f3n.</span>';
            });
        });

        // Allow Enter key
        newTagInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addTagBtn.click();
            }
        });
    }
});
