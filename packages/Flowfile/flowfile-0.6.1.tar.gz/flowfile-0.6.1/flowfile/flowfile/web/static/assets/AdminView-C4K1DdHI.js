import { k as axios, d as defineComponent, u as useAuthStore, J as onMounted, c as createElementBlock, z as createVNode, B as withCtx, ar as Transition, a as createBaseVNode, w as withModifiers, h as withDirectives, v as vModelText, i as vModelDynamic, n as normalizeClass, f as createTextVNode, e as createCommentVNode, ay as vModelCheckbox, t as toDisplayString, K as Fragment, L as renderList, G as computed, r as ref, o as openBlock, g as _export_sfc } from "./index-bcuE0Z0p.js";
class UserService {
  /**
   * Get all users (admin only)
   */
  async getUsers() {
    const response = await axios.get("/auth/users");
    return response.data;
  }
  /**
   * Create a new user (admin only)
   */
  async createUser(userData) {
    const response = await axios.post("/auth/users", userData);
    return response.data;
  }
  /**
   * Update a user (admin only)
   */
  async updateUser(userId, userData) {
    const response = await axios.put(`/auth/users/${userId}`, userData);
    return response.data;
  }
  /**
   * Delete a user (admin only)
   */
  async deleteUser(userId) {
    await axios.delete(`/auth/users/${userId}`);
  }
}
const userService = new UserService();
const _hoisted_1 = { class: "admin-container" };
const _hoisted_2 = { class: "card mb-3" };
const _hoisted_3 = { class: "card-content" };
const _hoisted_4 = { class: "form-grid" };
const _hoisted_5 = { class: "form-field" };
const _hoisted_6 = { class: "form-field" };
const _hoisted_7 = { class: "password-field" };
const _hoisted_8 = ["type"];
const _hoisted_9 = {
  key: 0,
  class: "password-requirements"
};
const _hoisted_10 = { class: "form-field" };
const _hoisted_11 = { class: "form-field" };
const _hoisted_12 = { class: "form-field checkbox-field" };
const _hoisted_13 = { class: "checkbox-label" };
const _hoisted_14 = { class: "form-actions" };
const _hoisted_15 = ["disabled"];
const _hoisted_16 = { class: "card mb-3" };
const _hoisted_17 = { class: "card-header" };
const _hoisted_18 = { class: "card-title" };
const _hoisted_19 = {
  key: 0,
  class: "search-container"
};
const _hoisted_20 = { class: "card-content" };
const _hoisted_21 = {
  key: 0,
  class: "loading-state"
};
const _hoisted_22 = {
  key: 1,
  class: "empty-state"
};
const _hoisted_23 = {
  key: 2,
  class: "users-table-container"
};
const _hoisted_24 = { class: "users-table" };
const _hoisted_25 = { class: "user-cell" };
const _hoisted_26 = {
  key: 0,
  class: "badge badge-warning"
};
const _hoisted_27 = {
  key: 1,
  class: "badge badge-muted"
};
const _hoisted_28 = { class: "action-buttons" };
const _hoisted_29 = ["onClick"];
const _hoisted_30 = ["onClick"];
const _hoisted_31 = ["onClick"];
const _hoisted_32 = {
  key: 3,
  class: "empty-state"
};
const _hoisted_33 = { class: "modal-header" };
const _hoisted_34 = { class: "modal-title" };
const _hoisted_35 = { class: "modal-content" };
const _hoisted_36 = { class: "form-field" };
const _hoisted_37 = { class: "form-field" };
const _hoisted_38 = { class: "form-field" };
const _hoisted_39 = { class: "password-field" };
const _hoisted_40 = ["type"];
const _hoisted_41 = {
  key: 0,
  class: "checkbox-group"
};
const _hoisted_42 = { class: "checkbox-label" };
const _hoisted_43 = { class: "checkbox-label" };
const _hoisted_44 = { class: "modal-actions" };
const _hoisted_45 = ["disabled"];
const _hoisted_46 = {
  key: 0,
  class: "fas fa-spinner fa-spin"
};
const _hoisted_47 = { class: "modal-content" };
const _hoisted_48 = { class: "modal-actions" };
const _hoisted_49 = ["disabled"];
const _hoisted_50 = {
  key: 0,
  class: "fas fa-spinner fa-spin"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "AdminView",
  setup(__props) {
    const authStore = useAuthStore();
    const currentUserId = computed(() => {
      var _a;
      return (_a = authStore.currentUser) == null ? void 0 : _a.id;
    });
    const users = ref([]);
    const isLoading = ref(false);
    const searchTerm = ref("");
    const newUser = ref({
      username: "",
      password: "",
      email: "",
      full_name: "",
      is_admin: false
    });
    const showNewPassword = ref(false);
    const isSubmitting = ref(false);
    const passwordChecks = computed(() => ({
      minLength: newUser.value.password.length >= 8,
      hasNumber: /\d/.test(newUser.value.password),
      hasSpecial: /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(newUser.value.password)
    }));
    const isPasswordValid = computed(
      () => passwordChecks.value.minLength && passwordChecks.value.hasNumber && passwordChecks.value.hasSpecial
    );
    const showEditModal = ref(false);
    const editUser = ref(null);
    const editFormData = ref({});
    const showEditPassword = ref(false);
    const isUpdating = ref(false);
    const showDeleteModal = ref(false);
    const userToDelete = ref(null);
    const isDeleting = ref(false);
    const filteredUsers = computed(() => {
      if (!searchTerm.value) return users.value;
      const term = searchTerm.value.toLowerCase();
      return users.value.filter(
        (user) => {
          var _a, _b;
          return user.username.toLowerCase().includes(term) || ((_a = user.email) == null ? void 0 : _a.toLowerCase().includes(term)) || ((_b = user.full_name) == null ? void 0 : _b.toLowerCase().includes(term));
        }
      );
    });
    const loadUsers = async () => {
      isLoading.value = true;
      try {
        users.value = await userService.getUsers();
      } catch (error) {
        console.error("Failed to load users:", error);
        showStatus("error", "Failed to load users. Please try again.");
      } finally {
        isLoading.value = false;
      }
    };
    const statusMessage = ref(null);
    const showStatus = (type, text) => {
      statusMessage.value = { type, text };
      setTimeout(() => {
        statusMessage.value = null;
      }, 4e3);
    };
    const getErrorMessage = (error) => {
      var _a, _b;
      const axiosError = error;
      return ((_b = (_a = axiosError.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || (error instanceof Error ? error.message : "An error occurred");
    };
    const handleAddUser = async () => {
      if (!newUser.value.username || !newUser.value.password) return;
      isSubmitting.value = true;
      try {
        await userService.createUser(newUser.value);
        newUser.value = { username: "", password: "", email: "", full_name: "", is_admin: false };
        showNewPassword.value = false;
        await loadUsers();
        showStatus("success", "User created successfully");
      } catch (error) {
        showStatus("error", getErrorMessage(error));
      } finally {
        isSubmitting.value = false;
      }
    };
    const openEditModal = (user) => {
      editUser.value = user;
      editFormData.value = {
        email: user.email || "",
        full_name: user.full_name || "",
        is_admin: user.is_admin,
        disabled: user.disabled,
        password: ""
      };
      showEditModal.value = true;
    };
    const closeEditModal = () => {
      showEditModal.value = false;
      editUser.value = null;
      editFormData.value = {};
      showEditPassword.value = false;
    };
    const handleUpdateUser = async () => {
      if (!editUser.value) return;
      isUpdating.value = true;
      try {
        const updateData = {};
        if (editFormData.value.email !== editUser.value.email) {
          updateData.email = editFormData.value.email;
        }
        if (editFormData.value.full_name !== editUser.value.full_name) {
          updateData.full_name = editFormData.value.full_name;
        }
        if (editFormData.value.is_admin !== editUser.value.is_admin) {
          updateData.is_admin = editFormData.value.is_admin;
        }
        if (editFormData.value.disabled !== editUser.value.disabled) {
          updateData.disabled = editFormData.value.disabled;
        }
        if (editFormData.value.password) {
          updateData.password = editFormData.value.password;
        }
        await userService.updateUser(editUser.value.id, updateData);
        closeEditModal();
        await loadUsers();
        showStatus("success", "User updated successfully");
      } catch (error) {
        showStatus("error", getErrorMessage(error));
      } finally {
        isUpdating.value = false;
      }
    };
    const openDeleteModal = (user) => {
      userToDelete.value = user;
      showDeleteModal.value = true;
    };
    const closeDeleteModal = () => {
      showDeleteModal.value = false;
      userToDelete.value = null;
    };
    const handleDeleteUser = async () => {
      if (!userToDelete.value) return;
      isDeleting.value = true;
      try {
        await userService.deleteUser(userToDelete.value.id);
        closeDeleteModal();
        await loadUsers();
        showStatus("success", "User deleted successfully");
      } catch (error) {
        showStatus("error", getErrorMessage(error));
      } finally {
        isDeleting.value = false;
      }
    };
    const handleForcePasswordChange = async (user) => {
      try {
        await userService.updateUser(user.id, { must_change_password: true });
        await loadUsers();
        showStatus("success", `${user.username} will be required to change password on next login`);
      } catch (error) {
        showStatus("error", getErrorMessage(error));
      }
    };
    onMounted(() => {
      loadUsers();
    });
    return (_ctx, _cache) => {
      var _a, _b, _c;
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(Transition, { name: "fade" }, {
          default: withCtx(() => [
            statusMessage.value ? (openBlock(), createElementBlock("div", {
              key: 0,
              class: normalizeClass(["status-message", `status-${statusMessage.value.type}`])
            }, [
              createBaseVNode("i", {
                class: normalizeClass(
                  statusMessage.value.type === "success" ? "fa-solid fa-check-circle" : "fa-solid fa-exclamation-circle"
                )
              }, null, 2),
              createBaseVNode("span", null, toDisplayString(statusMessage.value.text), 1)
            ], 2)) : createCommentVNode("", true)
          ]),
          _: 1
        }),
        _cache[47] || (_cache[47] = createBaseVNode("div", { class: "mb-3" }, [
          createBaseVNode("h2", { class: "page-title" }, "User Management"),
          createBaseVNode("p", { class: "page-description" }, "Manage users and their permissions")
        ], -1)),
        createBaseVNode("div", _hoisted_2, [
          _cache[24] || (_cache[24] = createBaseVNode("div", { class: "card-header" }, [
            createBaseVNode("h3", { class: "card-title" }, "Add New User")
          ], -1)),
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("form", {
              class: "form",
              onSubmit: withModifiers(handleAddUser, ["prevent"])
            }, [
              createBaseVNode("div", _hoisted_4, [
                createBaseVNode("div", _hoisted_5, [
                  _cache[15] || (_cache[15] = createBaseVNode("label", {
                    for: "new-username",
                    class: "form-label"
                  }, "Username", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "new-username",
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => newUser.value.username = $event),
                    type: "text",
                    class: "form-input",
                    placeholder: "Enter username",
                    required: ""
                  }, null, 512), [
                    [vModelText, newUser.value.username]
                  ])
                ]),
                createBaseVNode("div", _hoisted_6, [
                  _cache[19] || (_cache[19] = createBaseVNode("label", {
                    for: "new-password",
                    class: "form-label"
                  }, "Password", -1)),
                  createBaseVNode("div", _hoisted_7, [
                    withDirectives(createBaseVNode("input", {
                      id: "new-password",
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => newUser.value.password = $event),
                      type: showNewPassword.value ? "text" : "password",
                      class: "form-input",
                      placeholder: "Enter password",
                      required: ""
                    }, null, 8, _hoisted_8), [
                      [vModelDynamic, newUser.value.password]
                    ]),
                    createBaseVNode("button", {
                      type: "button",
                      class: "toggle-visibility",
                      "aria-label": "Toggle password visibility",
                      onClick: _cache[2] || (_cache[2] = ($event) => showNewPassword.value = !showNewPassword.value)
                    }, [
                      createBaseVNode("i", {
                        class: normalizeClass(showNewPassword.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                      }, null, 2)
                    ])
                  ]),
                  newUser.value.password ? (openBlock(), createElementBlock("ul", _hoisted_9, [
                    createBaseVNode("li", {
                      class: normalizeClass({ valid: passwordChecks.value.minLength })
                    }, [
                      createBaseVNode("i", {
                        class: normalizeClass(passwordChecks.value.minLength ? "fa-solid fa-check" : "fa-solid fa-times")
                      }, null, 2),
                      _cache[16] || (_cache[16] = createTextVNode(" 8+ characters ", -1))
                    ], 2),
                    createBaseVNode("li", {
                      class: normalizeClass({ valid: passwordChecks.value.hasNumber })
                    }, [
                      createBaseVNode("i", {
                        class: normalizeClass(passwordChecks.value.hasNumber ? "fa-solid fa-check" : "fa-solid fa-times")
                      }, null, 2),
                      _cache[17] || (_cache[17] = createTextVNode(" Number ", -1))
                    ], 2),
                    createBaseVNode("li", {
                      class: normalizeClass({ valid: passwordChecks.value.hasSpecial })
                    }, [
                      createBaseVNode("i", {
                        class: normalizeClass(passwordChecks.value.hasSpecial ? "fa-solid fa-check" : "fa-solid fa-times")
                      }, null, 2),
                      _cache[18] || (_cache[18] = createTextVNode(" Special char ", -1))
                    ], 2)
                  ])) : createCommentVNode("", true)
                ]),
                createBaseVNode("div", _hoisted_10, [
                  _cache[20] || (_cache[20] = createBaseVNode("label", {
                    for: "new-email",
                    class: "form-label"
                  }, "Email (optional)", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "new-email",
                    "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => newUser.value.email = $event),
                    type: "email",
                    class: "form-input",
                    placeholder: "user@example.com"
                  }, null, 512), [
                    [vModelText, newUser.value.email]
                  ])
                ]),
                createBaseVNode("div", _hoisted_11, [
                  _cache[21] || (_cache[21] = createBaseVNode("label", {
                    for: "new-fullname",
                    class: "form-label"
                  }, "Full Name (optional)", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "new-fullname",
                    "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => newUser.value.full_name = $event),
                    type: "text",
                    class: "form-input",
                    placeholder: "John Doe"
                  }, null, 512), [
                    [vModelText, newUser.value.full_name]
                  ])
                ]),
                createBaseVNode("div", _hoisted_12, [
                  createBaseVNode("label", _hoisted_13, [
                    withDirectives(createBaseVNode("input", {
                      "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => newUser.value.is_admin = $event),
                      type: "checkbox",
                      class: "form-checkbox"
                    }, null, 512), [
                      [vModelCheckbox, newUser.value.is_admin]
                    ]),
                    _cache[22] || (_cache[22] = createBaseVNode("span", null, "Administrator", -1))
                  ])
                ])
              ]),
              createBaseVNode("div", _hoisted_14, [
                createBaseVNode("button", {
                  type: "submit",
                  class: "btn btn-primary",
                  disabled: !newUser.value.username || !isPasswordValid.value || isSubmitting.value
                }, [
                  _cache[23] || (_cache[23] = createBaseVNode("i", { class: "fa-solid fa-user-plus" }, null, -1)),
                  createTextVNode(" " + toDisplayString(isSubmitting.value ? "Creating..." : "Create User"), 1)
                ], 8, _hoisted_15)
              ])
            ], 32)
          ])
        ]),
        createBaseVNode("div", _hoisted_16, [
          createBaseVNode("div", _hoisted_17, [
            createBaseVNode("h3", _hoisted_18, "Users (" + toDisplayString(filteredUsers.value.length) + ")", 1),
            users.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_19, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => searchTerm.value = $event),
                type: "text",
                placeholder: "Search users...",
                class: "search-input",
                "aria-label": "Search users"
              }, null, 512), [
                [vModelText, searchTerm.value]
              ]),
              _cache[25] || (_cache[25] = createBaseVNode("i", { class: "fa-solid fa-search search-icon" }, null, -1))
            ])) : createCommentVNode("", true)
          ]),
          createBaseVNode("div", _hoisted_20, [
            isLoading.value ? (openBlock(), createElementBlock("div", _hoisted_21, [..._cache[26] || (_cache[26] = [
              createBaseVNode("div", { class: "loading-spinner" }, null, -1),
              createBaseVNode("p", null, "Loading users...", -1)
            ])])) : !isLoading.value && users.value.length === 0 ? (openBlock(), createElementBlock("div", _hoisted_22, [..._cache[27] || (_cache[27] = [
              createBaseVNode("i", { class: "fa-solid fa-users" }, null, -1),
              createBaseVNode("p", null, "No users found", -1)
            ])])) : filteredUsers.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_23, [
              createBaseVNode("table", _hoisted_24, [
                _cache[34] || (_cache[34] = createBaseVNode("thead", null, [
                  createBaseVNode("tr", null, [
                    createBaseVNode("th", null, "Username"),
                    createBaseVNode("th", null, "Email"),
                    createBaseVNode("th", null, "Full Name"),
                    createBaseVNode("th", null, "Admin"),
                    createBaseVNode("th", null, "Status"),
                    createBaseVNode("th", null, "Password"),
                    createBaseVNode("th", null, "Actions")
                  ])
                ], -1)),
                createBaseVNode("tbody", null, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(filteredUsers.value, (user) => {
                    return openBlock(), createElementBlock("tr", {
                      key: user.id,
                      class: normalizeClass({ "disabled-row": user.disabled })
                    }, [
                      createBaseVNode("td", null, [
                        createBaseVNode("div", _hoisted_25, [
                          _cache[28] || (_cache[28] = createBaseVNode("i", { class: "fa-solid fa-user" }, null, -1)),
                          createBaseVNode("span", null, toDisplayString(user.username), 1)
                        ])
                      ]),
                      createBaseVNode("td", null, toDisplayString(user.email || "-"), 1),
                      createBaseVNode("td", null, toDisplayString(user.full_name || "-"), 1),
                      createBaseVNode("td", null, [
                        createBaseVNode("span", {
                          class: normalizeClass(["badge", user.is_admin ? "badge-primary" : "badge-secondary"])
                        }, toDisplayString(user.is_admin ? "Admin" : "User"), 3)
                      ]),
                      createBaseVNode("td", null, [
                        createBaseVNode("span", {
                          class: normalizeClass(["badge", user.disabled ? "badge-danger" : "badge-success"])
                        }, toDisplayString(user.disabled ? "Disabled" : "Active"), 3)
                      ]),
                      createBaseVNode("td", null, [
                        user.must_change_password ? (openBlock(), createElementBlock("span", _hoisted_26, [..._cache[29] || (_cache[29] = [
                          createBaseVNode("i", { class: "fa-solid fa-exclamation-triangle" }, null, -1),
                          createTextVNode(" Must Change ", -1)
                        ])])) : (openBlock(), createElementBlock("span", _hoisted_27, [..._cache[30] || (_cache[30] = [
                          createBaseVNode("i", { class: "fa-solid fa-check" }, null, -1),
                          createTextVNode(" OK ", -1)
                        ])]))
                      ]),
                      createBaseVNode("td", null, [
                        createBaseVNode("div", _hoisted_28, [
                          createBaseVNode("button", {
                            type: "button",
                            class: "btn btn-sm btn-secondary",
                            title: "Edit user",
                            onClick: ($event) => openEditModal(user)
                          }, [..._cache[31] || (_cache[31] = [
                            createBaseVNode("i", { class: "fa-solid fa-edit" }, null, -1)
                          ])], 8, _hoisted_29),
                          !user.must_change_password ? (openBlock(), createElementBlock("button", {
                            key: 0,
                            type: "button",
                            class: "btn btn-sm btn-warning",
                            title: "Force password change",
                            onClick: ($event) => handleForcePasswordChange(user)
                          }, [..._cache[32] || (_cache[32] = [
                            createBaseVNode("i", { class: "fa-solid fa-key" }, null, -1)
                          ])], 8, _hoisted_30)) : createCommentVNode("", true),
                          user.id !== currentUserId.value ? (openBlock(), createElementBlock("button", {
                            key: 1,
                            type: "button",
                            class: "btn btn-sm btn-danger",
                            title: "Delete user",
                            onClick: ($event) => openDeleteModal(user)
                          }, [..._cache[33] || (_cache[33] = [
                            createBaseVNode("i", { class: "fa-solid fa-trash-alt" }, null, -1)
                          ])], 8, _hoisted_31)) : createCommentVNode("", true)
                        ])
                      ])
                    ], 2);
                  }), 128))
                ])
              ])
            ])) : (openBlock(), createElementBlock("div", _hoisted_32, [
              _cache[35] || (_cache[35] = createBaseVNode("i", { class: "fa-solid fa-search" }, null, -1)),
              createBaseVNode("p", null, 'No users found matching "' + toDisplayString(searchTerm.value) + '"', 1)
            ]))
          ])
        ]),
        showEditModal.value ? (openBlock(), createElementBlock("div", {
          key: 0,
          class: "modal-overlay",
          onClick: closeEditModal
        }, [
          createBaseVNode("div", {
            class: "modal-container",
            onClick: _cache[13] || (_cache[13] = withModifiers(() => {
            }, ["stop"]))
          }, [
            createBaseVNode("div", _hoisted_33, [
              createBaseVNode("h3", _hoisted_34, "Edit User: " + toDisplayString((_a = editUser.value) == null ? void 0 : _a.username), 1),
              createBaseVNode("button", {
                class: "modal-close",
                "aria-label": "Close",
                onClick: closeEditModal
              }, [..._cache[36] || (_cache[36] = [
                createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
              ])])
            ]),
            createBaseVNode("div", _hoisted_35, [
              createBaseVNode("form", {
                onSubmit: withModifiers(handleUpdateUser, ["prevent"])
              }, [
                createBaseVNode("div", _hoisted_36, [
                  _cache[37] || (_cache[37] = createBaseVNode("label", { class: "form-label" }, "Email", -1)),
                  withDirectives(createBaseVNode("input", {
                    "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => editFormData.value.email = $event),
                    type: "email",
                    class: "form-input",
                    placeholder: "user@example.com"
                  }, null, 512), [
                    [vModelText, editFormData.value.email]
                  ])
                ]),
                createBaseVNode("div", _hoisted_37, [
                  _cache[38] || (_cache[38] = createBaseVNode("label", { class: "form-label" }, "Full Name", -1)),
                  withDirectives(createBaseVNode("input", {
                    "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => editFormData.value.full_name = $event),
                    type: "text",
                    class: "form-input",
                    placeholder: "John Doe"
                  }, null, 512), [
                    [vModelText, editFormData.value.full_name]
                  ])
                ]),
                createBaseVNode("div", _hoisted_38, [
                  _cache[39] || (_cache[39] = createBaseVNode("label", { class: "form-label" }, "New Password (leave blank to keep current)", -1)),
                  createBaseVNode("div", _hoisted_39, [
                    withDirectives(createBaseVNode("input", {
                      "onUpdate:modelValue": _cache[9] || (_cache[9] = ($event) => editFormData.value.password = $event),
                      type: showEditPassword.value ? "text" : "password",
                      class: "form-input",
                      placeholder: "Enter new password"
                    }, null, 8, _hoisted_40), [
                      [vModelDynamic, editFormData.value.password]
                    ]),
                    createBaseVNode("button", {
                      type: "button",
                      class: "toggle-visibility",
                      "aria-label": "Toggle password visibility",
                      onClick: _cache[10] || (_cache[10] = ($event) => showEditPassword.value = !showEditPassword.value)
                    }, [
                      createBaseVNode("i", {
                        class: normalizeClass(showEditPassword.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                      }, null, 2)
                    ])
                  ])
                ]),
                ((_b = editUser.value) == null ? void 0 : _b.id) !== currentUserId.value ? (openBlock(), createElementBlock("div", _hoisted_41, [
                  createBaseVNode("label", _hoisted_42, [
                    withDirectives(createBaseVNode("input", {
                      "onUpdate:modelValue": _cache[11] || (_cache[11] = ($event) => editFormData.value.is_admin = $event),
                      type: "checkbox",
                      class: "form-checkbox"
                    }, null, 512), [
                      [vModelCheckbox, editFormData.value.is_admin]
                    ]),
                    _cache[40] || (_cache[40] = createBaseVNode("span", null, "Administrator", -1))
                  ]),
                  createBaseVNode("label", _hoisted_43, [
                    withDirectives(createBaseVNode("input", {
                      "onUpdate:modelValue": _cache[12] || (_cache[12] = ($event) => editFormData.value.disabled = $event),
                      type: "checkbox",
                      class: "form-checkbox"
                    }, null, 512), [
                      [vModelCheckbox, editFormData.value.disabled]
                    ]),
                    _cache[41] || (_cache[41] = createBaseVNode("span", null, "Disabled", -1))
                  ])
                ])) : createCommentVNode("", true)
              ], 32)
            ]),
            createBaseVNode("div", _hoisted_44, [
              createBaseVNode("button", {
                class: "btn btn-secondary",
                onClick: closeEditModal
              }, "Cancel"),
              createBaseVNode("button", {
                class: "btn btn-primary",
                disabled: isUpdating.value,
                onClick: handleUpdateUser
              }, [
                isUpdating.value ? (openBlock(), createElementBlock("i", _hoisted_46)) : createCommentVNode("", true),
                createTextVNode(" " + toDisplayString(isUpdating.value ? "Saving..." : "Save Changes"), 1)
              ], 8, _hoisted_45)
            ])
          ])
        ])) : createCommentVNode("", true),
        showDeleteModal.value ? (openBlock(), createElementBlock("div", {
          key: 1,
          class: "modal-overlay",
          onClick: closeDeleteModal
        }, [
          createBaseVNode("div", {
            class: "modal-container",
            onClick: _cache[14] || (_cache[14] = withModifiers(() => {
            }, ["stop"]))
          }, [
            createBaseVNode("div", { class: "modal-header" }, [
              _cache[43] || (_cache[43] = createBaseVNode("h3", { class: "modal-title" }, "Delete User", -1)),
              createBaseVNode("button", {
                class: "modal-close",
                "aria-label": "Close",
                onClick: closeDeleteModal
              }, [..._cache[42] || (_cache[42] = [
                createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
              ])])
            ]),
            createBaseVNode("div", _hoisted_47, [
              createBaseVNode("p", null, [
                _cache[44] || (_cache[44] = createTextVNode(" Are you sure you want to delete the user ", -1)),
                createBaseVNode("strong", null, toDisplayString((_c = userToDelete.value) == null ? void 0 : _c.username), 1),
                _cache[45] || (_cache[45] = createTextVNode("? ", -1))
              ]),
              _cache[46] || (_cache[46] = createBaseVNode("p", { class: "warning-text" }, " This will also delete all their secrets, database connections, and cloud connections. This action cannot be undone. ", -1))
            ]),
            createBaseVNode("div", _hoisted_48, [
              createBaseVNode("button", {
                class: "btn btn-secondary",
                onClick: closeDeleteModal
              }, "Cancel"),
              createBaseVNode("button", {
                class: "btn btn-danger-filled",
                disabled: isDeleting.value,
                onClick: handleDeleteUser
              }, [
                isDeleting.value ? (openBlock(), createElementBlock("i", _hoisted_50)) : createCommentVNode("", true),
                createTextVNode(" " + toDisplayString(isDeleting.value ? "Deleting..." : "Delete User"), 1)
              ], 8, _hoisted_49)
            ])
          ])
        ])) : createCommentVNode("", true)
      ]);
    };
  }
});
const AdminView = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-4d1a7404"]]);
export {
  AdminView as default
};
