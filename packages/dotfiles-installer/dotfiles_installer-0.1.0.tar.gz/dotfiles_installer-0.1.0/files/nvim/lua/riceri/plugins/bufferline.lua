return {
    'akinsho/bufferline.nvim',
    version = "*",
    dependencies = 'nvim-tree/nvim-web-devicons',
    config = function()
        require('bufferline').setup{
            options = {
                diagnostics = "nvim_lsp",
                separator = true,
                separator_style = "slant",
                auto_toggle_bufferline = true,
                show_buffer_close_icons = false,
                offsets = {
                    {
                        filetype = "NvimTree",
                        text = "File Explorer",
                        seperator = true,
                    }
                },
                custom_filter = function(buf_num)
                    local ft = vim.bo[buf_num].filetype
                    return ft ~= "fugitive" and ft ~= "git" and ft ~= "gitcommit"
                end,
            },
            highlights = {
                fill = {
                    bg = "#000000",
                    fg = "#000000",
                },
                separator = {
                    fg = "#000000",
                },
                separator_selected = {
                    fg = "#000000",
                },
                separator_visible = {
                    fg = "#000000",
                },
            }
        }

        vim.keymap.set("n", "<tab>", "<cmd>BufferLineCycleNext<cr>")
        vim.keymap.set("n", "<S-Tab>", "<cmd>BufferLineCyclePrev<cr>")

        vim.keymap.set("n", "<leader>xx", "<cmd>bdelete<cr>")
        vim.keymap.set("n", "<leader>xa", function()
            local current_buf = vim.api.nvim_get_current_buf()
            local buffers = vim.api.nvim_list_bufs()

            for _, buffnr in ipairs(buffers) do
                if buffnr ~= current_buf and vim.api.nvim_buf_is_loaded(buffnr) then
                    vim.cmd("bdelete " .. buffnr)
                end
            end
        end)
    end,
}
