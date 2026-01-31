return {
    "nvim-tree/nvim-tree.lua",
    version = "*",
    lazy = false,
    dependencies = {
        "nvim-tree/nvim-web-devicons",
    },
    config = function()
        require("nvim-tree").setup{
            filters = { dotfiles = false },
            disable_netrw = true,
            hijack_cursor = true,
            sync_root_with_cwd = true,
            update_focused_file = {
                enable = true,
                update_root = false,
            },
            git = {
                ignore = false,
            },
            view = {
                width = 30,
                preserve_window_proportions = true,
            },
            renderer = {
                root_folder_label = false,
                highlight_git = true,
                indent_markers = { enable = true },
                icons = {
                    glyphs = {
                        default = "󰈚",
                        folder = {
                            default = "",
                            empty = "",
                            empty_open = "",
                            open = "",
                            symlink = "",
                        },
                        git = { unmerged = "" },
                    },
                },
            },
            actions = {
                open_file = {
                    quit_on_open = true,
                },
            },
        }

        local Riceri_Tree = vim.api.nvim_create_augroup("Riceri_Tree", {})

        local autocmd = vim.api.nvim_create_autocmd
        autocmd("BufEnter", {
            group = Riceri_Tree,
            callback = function()
                if vim.fn.bufname() ~= 'NvimTree' and vim.bo.filetype ~= 'NvimTree' and vim.fn.bufexists('NvimTree') == 1 then
                    require("nvim-tree").toggle(false)
                end
            end,
        })
    end,
}
