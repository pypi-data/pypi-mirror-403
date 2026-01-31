// MPS Correlation - Metal implementation of correlation for optical flow
// Used in RAFT, PWC-Net, FlowNet, etc.

#include <torch/extension.h>
#include <ATen/native/mps/OperationUtils.h>
#include <Metal/Metal.h>
#include <Foundation/Foundation.h>

static id<MTLDevice> g_device = nil;
static id<MTLLibrary> g_library = nil;
static id<MTLComputePipelineState> g_corr_forward_fp32 = nil;
static id<MTLComputePipelineState> g_corr_forward_fp16 = nil;
static id<MTLComputePipelineState> g_corr_backward_input1_fp32 = nil;
static id<MTLComputePipelineState> g_corr_backward_input2_fp32 = nil;

static const char* METAL_SHADER = R"(
#include <metal_stdlib>
using namespace metal;

// Forward correlation kernel
// Reference: https://github.com/ClementPinard/Pytorch-Correlation-extension
// Conceptually works on zero-padded inputs. Coordinates are in padded space,
// then converted to original image space with bounds checking.
kernel void correlation_forward_fp32(
    device const float* input1 [[buffer(0)]],
    device const float* input2 [[buffer(1)]],
    device float* output [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& height [[buffer(5)]],
    constant int& width [[buffer(6)]],
    constant int& kernel_size [[buffer(7)]],
    constant int& max_displacement [[buffer(8)]],
    constant int& stride1 [[buffer(9)]],
    constant int& stride2 [[buffer(10)]],
    constant int& pad_size [[buffer(11)]],
    constant int& is_multiply [[buffer(12)]],
    constant int& out_channels [[buffer(13)]],
    constant int& out_height [[buffer(14)]],
    constant int& out_width [[buffer(15)]],
    uint3 gid [[thread_position_in_grid]]
) {
    int w = gid.x;
    int h = gid.y;
    int bc = gid.z;  // batch * out_channels

    int b = bc / out_channels;
    int c = bc % out_channels;

    if (w >= out_width || h >= out_height || b >= batch) return;

    int neighborhood_size = 2 * max_displacement / stride2 + 1;
    int dy = c / neighborhood_size - max_displacement / stride2;
    int dx = c % neighborhood_size - max_displacement / stride2;

    dy *= stride2;
    dx *= stride2;

    // Output position maps to center of correlation window
    // In padded space, output (0,0) corresponds to position (max_displacement, max_displacement)
    // which maps to original image position (max_displacement - pad_size, max_displacement - pad_size)
    int x1 = w * stride1 + max_displacement - pad_size;
    int y1 = h * stride1 + max_displacement - pad_size;

    int x2 = x1 + dx;
    int y2 = y1 + dy;

    float sum = 0.0f;
    int k_rad = kernel_size / 2;

    for (int kc = 0; kc < channels; kc++) {
        for (int ky = -k_rad; ky <= k_rad; ky++) {
            for (int kx = -k_rad; kx <= k_rad; kx++) {
                int py1 = y1 + ky;
                int px1 = x1 + kx;
                int py2 = y2 + ky;
                int px2 = x2 + kx;

                float v1 = 0.0f, v2 = 0.0f;

                if (py1 >= 0 && py1 < height && px1 >= 0 && px1 < width) {
                    v1 = input1[b * channels * height * width + kc * height * width + py1 * width + px1];
                }
                if (py2 >= 0 && py2 < height && px2 >= 0 && px2 < width) {
                    v2 = input2[b * channels * height * width + kc * height * width + py2 * width + px2];
                }

                if (is_multiply) {
                    sum += v1 * v2;
                } else {
                    float diff = v1 - v2;
                    sum += diff * diff;
                }
            }
        }
    }

    output[b * out_channels * out_height * out_width + c * out_height * out_width + h * out_width + w] = sum;
}

kernel void correlation_forward_fp16(
    device const half* input1 [[buffer(0)]],
    device const half* input2 [[buffer(1)]],
    device half* output [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& height [[buffer(5)]],
    constant int& width [[buffer(6)]],
    constant int& kernel_size [[buffer(7)]],
    constant int& max_displacement [[buffer(8)]],
    constant int& stride1 [[buffer(9)]],
    constant int& stride2 [[buffer(10)]],
    constant int& pad_size [[buffer(11)]],
    constant int& is_multiply [[buffer(12)]],
    constant int& out_channels [[buffer(13)]],
    constant int& out_height [[buffer(14)]],
    constant int& out_width [[buffer(15)]],
    uint3 gid [[thread_position_in_grid]]
) {
    int w = gid.x;
    int h = gid.y;
    int bc = gid.z;

    int b = bc / out_channels;
    int c = bc % out_channels;

    if (w >= out_width || h >= out_height || b >= batch) return;

    int neighborhood_size = 2 * max_displacement / stride2 + 1;
    int dy = c / neighborhood_size - max_displacement / stride2;
    int dx = c % neighborhood_size - max_displacement / stride2;

    dy *= stride2;
    dx *= stride2;

    int x1 = w * stride1 + max_displacement - pad_size;
    int y1 = h * stride1 + max_displacement - pad_size;

    int x2 = x1 + dx;
    int y2 = y1 + dy;

    float sum = 0.0f;
    int k_rad = kernel_size / 2;

    for (int kc = 0; kc < channels; kc++) {
        for (int ky = -k_rad; ky <= k_rad; ky++) {
            for (int kx = -k_rad; kx <= k_rad; kx++) {
                int py1 = y1 + ky;
                int px1 = x1 + kx;
                int py2 = y2 + ky;
                int px2 = x2 + kx;

                float v1 = 0.0f, v2 = 0.0f;

                if (py1 >= 0 && py1 < height && px1 >= 0 && px1 < width) {
                    v1 = float(input1[b * channels * height * width + kc * height * width + py1 * width + px1]);
                }
                if (py2 >= 0 && py2 < height && px2 >= 0 && px2 < width) {
                    v2 = float(input2[b * channels * height * width + kc * height * width + py2 * width + px2]);
                }

                if (is_multiply) {
                    sum += v1 * v2;
                } else {
                    float diff = v1 - v2;
                    sum += diff * diff;
                }
            }
        }
    }

    output[b * out_channels * out_height * out_width + c * out_height * out_width + h * out_width + w] = half(sum);
}

// Backward for input1 - iterate over output and scatter gradients
kernel void correlation_backward_input1_fp32(
    device const float* grad_output [[buffer(0)]],
    device const float* input2 [[buffer(1)]],
    device atomic_float* grad_input1 [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& height [[buffer(5)]],
    constant int& width [[buffer(6)]],
    constant int& kernel_size [[buffer(7)]],
    constant int& max_displacement [[buffer(8)]],
    constant int& stride1 [[buffer(9)]],
    constant int& stride2 [[buffer(10)]],
    constant int& pad_size [[buffer(11)]],
    constant int& is_multiply [[buffer(12)]],
    constant int& out_channels [[buffer(13)]],
    constant int& out_height [[buffer(14)]],
    constant int& out_width [[buffer(15)]],
    uint3 gid [[thread_position_in_grid]]
) {
    // Each thread handles one output position
    int ow = gid.x;
    int oh = gid.y;
    int bc = gid.z;  // batch * out_channels

    int b = bc / out_channels;
    int oc = bc % out_channels;

    if (ow >= out_width || oh >= out_height || b >= batch) return;

    int neighborhood_size = 2 * max_displacement / stride2 + 1;
    int dy_idx = oc / neighborhood_size;
    int dx_idx = oc % neighborhood_size;
    int dy = (dy_idx - max_displacement / stride2) * stride2;
    int dx = (dx_idx - max_displacement / stride2) * stride2;

    int k_rad = kernel_size / 2;

    // Same coordinate mapping as forward
    int x1_base = ow * stride1 + max_displacement - pad_size;
    int y1_base = oh * stride1 + max_displacement - pad_size;

    float grad_val = grad_output[b * out_channels * out_height * out_width +
                                  oc * out_height * out_width + oh * out_width + ow];

    for (int c = 0; c < channels; c++) {
        for (int ky = -k_rad; ky <= k_rad; ky++) {
            for (int kx = -k_rad; kx <= k_rad; kx++) {
                int y1 = y1_base + ky;
                int x1 = x1_base + kx;
                int y2 = y1_base + dy + ky;
                int x2 = x1_base + dx + kx;

                // grad_input1 gets gradient from input2 values
                if (y1 >= 0 && y1 < height && x1 >= 0 && x1 < width) {
                    float v2 = 0.0f;
                    if (y2 >= 0 && y2 < height && x2 >= 0 && x2 < width) {
                        v2 = input2[b * channels * height * width + c * height * width + y2 * width + x2];
                    }

                    if (is_multiply) {
                        int idx = b * channels * height * width + c * height * width + y1 * width + x1;
                        atomic_fetch_add_explicit(&grad_input1[idx], grad_val * v2, memory_order_relaxed);
                    }
                }
            }
        }
    }
}

// Backward for input2 - scatter gradients from output positions
kernel void correlation_backward_input2_fp32(
    device const float* grad_output [[buffer(0)]],
    device const float* input1 [[buffer(1)]],
    device atomic_float* grad_input2 [[buffer(2)]],
    constant int& batch [[buffer(3)]],
    constant int& channels [[buffer(4)]],
    constant int& height [[buffer(5)]],
    constant int& width [[buffer(6)]],
    constant int& kernel_size [[buffer(7)]],
    constant int& max_displacement [[buffer(8)]],
    constant int& stride1 [[buffer(9)]],
    constant int& stride2 [[buffer(10)]],
    constant int& pad_size [[buffer(11)]],
    constant int& is_multiply [[buffer(12)]],
    constant int& out_channels [[buffer(13)]],
    constant int& out_height [[buffer(14)]],
    constant int& out_width [[buffer(15)]],
    uint3 gid [[thread_position_in_grid]]
) {
    // Each thread handles one output position
    int ow = gid.x;
    int oh = gid.y;
    int bc = gid.z;  // batch * out_channels

    int b = bc / out_channels;
    int oc = bc % out_channels;

    if (ow >= out_width || oh >= out_height || b >= batch) return;

    int neighborhood_size = 2 * max_displacement / stride2 + 1;
    int dy_idx = oc / neighborhood_size;
    int dx_idx = oc % neighborhood_size;
    int dy = (dy_idx - max_displacement / stride2) * stride2;
    int dx = (dx_idx - max_displacement / stride2) * stride2;

    int k_rad = kernel_size / 2;

    // Same coordinate mapping as forward
    int x1_base = ow * stride1 + max_displacement - pad_size;
    int y1_base = oh * stride1 + max_displacement - pad_size;

    float grad_val = grad_output[b * out_channels * out_height * out_width +
                                  oc * out_height * out_width + oh * out_width + ow];

    for (int c = 0; c < channels; c++) {
        for (int ky = -k_rad; ky <= k_rad; ky++) {
            for (int kx = -k_rad; kx <= k_rad; kx++) {
                int y1 = y1_base + ky;
                int x1 = x1_base + kx;
                int y2 = y1_base + dy + ky;
                int x2 = x1_base + dx + kx;

                // grad_input2 gets gradient from input1 values
                if (y2 >= 0 && y2 < height && x2 >= 0 && x2 < width) {
                    float v1 = 0.0f;
                    if (y1 >= 0 && y1 < height && x1 >= 0 && x1 < width) {
                        v1 = input1[b * channels * height * width + c * height * width + y1 * width + x1];
                    }

                    if (is_multiply) {
                        int idx = b * channels * height * width + c * height * width + y2 * width + x2;
                        atomic_fetch_add_explicit(&grad_input2[idx], grad_val * v1, memory_order_relaxed);
                    }
                }
            }
        }
    }
}
)";

static void ensure_initialized() {
    if (g_device != nil) return;

    g_device = MTLCreateSystemDefaultDevice();
    NSError* error = nil;

    NSString* source = [NSString stringWithUTF8String:METAL_SHADER];
    g_library = [g_device newLibraryWithSource:source options:nil error:&error];

    if (error) {
        NSLog(@"Failed to compile Metal shader: %@", error);
        throw std::runtime_error("Failed to compile Metal shader");
    }

    id<MTLFunction> corr_fwd_fp32 = [g_library newFunctionWithName:@"correlation_forward_fp32"];
    id<MTLFunction> corr_fwd_fp16 = [g_library newFunctionWithName:@"correlation_forward_fp16"];
    id<MTLFunction> corr_bwd_in1 = [g_library newFunctionWithName:@"correlation_backward_input1_fp32"];
    id<MTLFunction> corr_bwd_in2 = [g_library newFunctionWithName:@"correlation_backward_input2_fp32"];

    g_corr_forward_fp32 = [g_device newComputePipelineStateWithFunction:corr_fwd_fp32 error:&error];
    g_corr_forward_fp16 = [g_device newComputePipelineStateWithFunction:corr_fwd_fp16 error:&error];
    g_corr_backward_input1_fp32 = [g_device newComputePipelineStateWithFunction:corr_bwd_in1 error:&error];
    g_corr_backward_input2_fp32 = [g_device newComputePipelineStateWithFunction:corr_bwd_in2 error:&error];
}

torch::Tensor correlation_forward_mps(
    const torch::Tensor& input1,
    const torch::Tensor& input2,
    int kernel_size,
    int max_displacement,
    int stride1,
    int stride2,
    int pad_size,
    bool is_multiply
) {
    ensure_initialized();

    TORCH_CHECK(input1.device().type() == torch::kMPS, "input1 must be on MPS");
    TORCH_CHECK(input2.device().type() == torch::kMPS, "input2 must be on MPS");
    TORCH_CHECK(input1.sizes() == input2.sizes(), "input1 and input2 must have same shape");

    int batch = input1.size(0);
    int channels = input1.size(1);
    int height = input1.size(2);
    int width = input1.size(3);

    int padded_height = height + 2 * pad_size;
    int padded_width = width + 2 * pad_size;

    int out_height = (padded_height - 2 * max_displacement - 1) / stride1 + 1;
    int out_width = (padded_width - 2 * max_displacement - 1) / stride1 + 1;
    int neighborhood_size = 2 * max_displacement / stride2 + 1;
    int out_channels = neighborhood_size * neighborhood_size;

    auto output = torch::zeros({batch, out_channels, out_height, out_width}, input1.options());

    // Ensure inputs are contiguous
    auto input1_contig = input1.contiguous();
    auto input2_contig = input2.contiguous();

    // Use MPS stream with PyTorch's shared encoder (zero-sync)
    @autoreleasepool {
        auto stream = at::mps::getCurrentMPSStream();
        id<MTLComputeCommandEncoder> encoder = stream->commandEncoder();

        bool is_fp16 = input1_contig.scalar_type() == torch::kHalf;
        id<MTLComputePipelineState> pso = is_fp16 ? g_corr_forward_fp16 : g_corr_forward_fp32;

        [encoder setComputePipelineState:pso];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(input1_contig) offset:0 atIndex:0];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(input2_contig) offset:0 atIndex:1];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(output) offset:0 atIndex:2];

        int is_mult_int = is_multiply ? 1 : 0;
        [encoder setBytes:&batch length:sizeof(int) atIndex:3];
        [encoder setBytes:&channels length:sizeof(int) atIndex:4];
        [encoder setBytes:&height length:sizeof(int) atIndex:5];
        [encoder setBytes:&width length:sizeof(int) atIndex:6];
        [encoder setBytes:&kernel_size length:sizeof(int) atIndex:7];
        [encoder setBytes:&max_displacement length:sizeof(int) atIndex:8];
        [encoder setBytes:&stride1 length:sizeof(int) atIndex:9];
        [encoder setBytes:&stride2 length:sizeof(int) atIndex:10];
        [encoder setBytes:&pad_size length:sizeof(int) atIndex:11];
        [encoder setBytes:&is_mult_int length:sizeof(int) atIndex:12];
        [encoder setBytes:&out_channels length:sizeof(int) atIndex:13];
        [encoder setBytes:&out_height length:sizeof(int) atIndex:14];
        [encoder setBytes:&out_width length:sizeof(int) atIndex:15];

        MTLSize gridSize = MTLSizeMake(out_width, out_height, batch * out_channels);
        MTLSize threadGroupSize = MTLSizeMake(8, 8, 1);
        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadGroupSize];

        // Don't endEncoding/commit - PyTorch manages encoder lifecycle
    }

    return output;
}

std::tuple<torch::Tensor, torch::Tensor> correlation_backward_mps(
    const torch::Tensor& grad_output,
    const torch::Tensor& input1,
    const torch::Tensor& input2,
    int kernel_size,
    int max_displacement,
    int stride1,
    int stride2,
    int pad_size,
    bool is_multiply
) {
    ensure_initialized();

    int batch = input1.size(0);
    int channels = input1.size(1);
    int height = input1.size(2);
    int width = input1.size(3);

    int padded_height = height + 2 * pad_size;
    int padded_width = width + 2 * pad_size;
    int out_height = (padded_height - 2 * max_displacement - 1) / stride1 + 1;
    int out_width = (padded_width - 2 * max_displacement - 1) / stride1 + 1;
    int neighborhood_size = 2 * max_displacement / stride2 + 1;
    int out_channels = neighborhood_size * neighborhood_size;

    // Convert to float32 for backward if needed and ensure contiguous
    auto grad_output_f = grad_output.to(torch::kFloat32).contiguous();
    auto input1_f = input1.to(torch::kFloat32).contiguous();
    auto input2_f = input2.to(torch::kFloat32).contiguous();
    auto grad_input1_f = torch::zeros_like(input1_f);
    auto grad_input2_f = torch::zeros_like(input2_f);

    // Use MPS stream with PyTorch's shared encoder (zero-sync)
    @autoreleasepool {
        auto stream = at::mps::getCurrentMPSStream();
        id<MTLComputeCommandEncoder> encoder = stream->commandEncoder();

        int is_mult_int = is_multiply ? 1 : 0;

        // Backward for input1
        [encoder setComputePipelineState:g_corr_backward_input1_fp32];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(grad_output_f) offset:0 atIndex:0];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(input2_f) offset:0 atIndex:1];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(grad_input1_f) offset:0 atIndex:2];
        [encoder setBytes:&batch length:sizeof(int) atIndex:3];
        [encoder setBytes:&channels length:sizeof(int) atIndex:4];
        [encoder setBytes:&height length:sizeof(int) atIndex:5];
        [encoder setBytes:&width length:sizeof(int) atIndex:6];
        [encoder setBytes:&kernel_size length:sizeof(int) atIndex:7];
        [encoder setBytes:&max_displacement length:sizeof(int) atIndex:8];
        [encoder setBytes:&stride1 length:sizeof(int) atIndex:9];
        [encoder setBytes:&stride2 length:sizeof(int) atIndex:10];
        [encoder setBytes:&pad_size length:sizeof(int) atIndex:11];
        [encoder setBytes:&is_mult_int length:sizeof(int) atIndex:12];
        [encoder setBytes:&out_channels length:sizeof(int) atIndex:13];
        [encoder setBytes:&out_height length:sizeof(int) atIndex:14];
        [encoder setBytes:&out_width length:sizeof(int) atIndex:15];

        // Grid over output positions (out_width, out_height, batch * out_channels)
        MTLSize gridSize = MTLSizeMake(out_width, out_height, batch * out_channels);
        MTLSize threadGroupSize = MTLSizeMake(8, 8, 1);
        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadGroupSize];

        // Backward for input2 - dispatch on same encoder (multiple dispatches allowed)
        [encoder setComputePipelineState:g_corr_backward_input2_fp32];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(grad_output_f) offset:0 atIndex:0];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(input1_f) offset:0 atIndex:1];
        [encoder setBuffer:at::native::mps::getMTLBufferStorage(grad_input2_f) offset:0 atIndex:2];
        [encoder setBytes:&batch length:sizeof(int) atIndex:3];
        [encoder setBytes:&channels length:sizeof(int) atIndex:4];
        [encoder setBytes:&height length:sizeof(int) atIndex:5];
        [encoder setBytes:&width length:sizeof(int) atIndex:6];
        [encoder setBytes:&kernel_size length:sizeof(int) atIndex:7];
        [encoder setBytes:&max_displacement length:sizeof(int) atIndex:8];
        [encoder setBytes:&stride1 length:sizeof(int) atIndex:9];
        [encoder setBytes:&stride2 length:sizeof(int) atIndex:10];
        [encoder setBytes:&pad_size length:sizeof(int) atIndex:11];
        [encoder setBytes:&is_mult_int length:sizeof(int) atIndex:12];
        [encoder setBytes:&out_channels length:sizeof(int) atIndex:13];
        [encoder setBytes:&out_height length:sizeof(int) atIndex:14];
        [encoder setBytes:&out_width length:sizeof(int) atIndex:15];

        [encoder dispatchThreads:gridSize threadsPerThreadgroup:threadGroupSize];

        // Don't endEncoding/commit - PyTorch manages encoder lifecycle
    }

    return std::make_tuple(
        grad_input1_f.to(input1.scalar_type()),
        grad_input2_f.to(input2.scalar_type())
    );
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("correlation_forward", &correlation_forward_mps, "Correlation forward (MPS)");
    m.def("correlation_backward", &correlation_backward_mps, "Correlation backward (MPS)");
}
